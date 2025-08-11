#!/usr/bin/env python3
"""TOVA v4 Menu-Driven TUI - Simple and reliable"""

import asyncio
import subprocess
import signal
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import time
from dataclasses import dataclass
from enum import Enum
from collections import deque
import threading
import requests
import json

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    from rich import box
except ImportError:
    print("Installing required package: rich")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich"])  # nosec - CLI utility install
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    from rich import box

console = Console()

class ServiceStatus(Enum):
    RUNNING = "[green]● Running[/green]"
    STOPPED = "[red]● Stopped[/red]"
    STARTING = "[yellow]● Starting[/yellow]"
    STOPPING = "[yellow]● Stopping[/yellow]"
    ERROR = "[red]● Error[/red]"

@dataclass
class Service:
    name: str
    display_name: str
    port: int
    pid_file: str
    log_file: str
    start_script: str
    health_endpoint: str
    health_method: str = "GET"
    status: ServiceStatus = ServiceStatus.STOPPED
    pid: Optional[int] = None
    log_process: Optional[subprocess.Popen] = None
    log_buffer: deque = None
    last_health_check: float = 0
    health_check_interval: float = 5.0  # seconds
    
    def __post_init__(self):
        if self.log_buffer is None:
            self.log_buffer = deque(maxlen=100)

class TovaTUIMenu:
    def __init__(self):
        self.project_root = Path("/home/anthon/t0v4")
        self.log_path = self.project_root / "data" / "logs"
        self.scripts_path = self.project_root / "scripts" / "start"
        
        # Ensure log directory exists
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        # Define services with correct script paths and health endpoints
        self.services: Dict[str, Service] = {
            "mixtral": Service(
                name="mixtral",
                display_name="🎭 Mixtral (Primary Brain)",
                port=8000,
                pid_file=str(self.log_path / "mixtral.pid"),
                log_file=str(self.log_path / "mixtral.log"),
                start_script=str(self.scripts_path / "start_mixtral.sh"),
                health_endpoint="/v1/models",
                health_method="GET"
            ),
            "phi": Service(
                name="phi",
                display_name="🔍 Phi (Background Brain)",
                port=8001,
                pid_file=str(self.log_path / "phi.pid"),
                log_file=str(self.log_path / "phi.log"),
                start_script=str(self.scripts_path / "start_phi.sh"),
                health_endpoint="/completion",
                health_method="POST"
            ),
            "tova": Service(
                name="tova",
                display_name="🎪 TOVA Core (main.py)",
                port=8002,
                pid_file=str(self.log_path / "tova.pid"),
                log_file=str(self.log_path / "tova.log"),
                start_script=str(self.scripts_path / "start_tova.sh"),
                health_endpoint="/health",
                health_method="GET"
            )
        }
        
        self.service_list = list(self.services.keys())
        self.running = True
        self.combined_logs = deque(maxlen=100)
        self.start_log_monitoring()
        
    def check_script_exists(self, script_path: str) -> bool:
        """Check if start script exists and is executable"""
        path = Path(script_path)
        return path.exists() and os.access(path, os.X_OK)
    
    def check_pid_file(self, service: Service) -> tuple[bool, int]:
        """Check if PID file exists and contains valid PID"""
        try:
            if not Path(service.pid_file).exists():
                return False, 0
            
            with open(service.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is actually running
            os.kill(pid, 0)  # Signal 0 just checks if process exists
            return True, pid
        except (OSError, ValueError, FileNotFoundError):
            return False, 0
    
    def check_port_usage(self, port: int) -> bool:
        """Check if port is in use"""
        try:
            result = subprocess.run(
                ["lsof", "-i", f":{port}"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0 and result.stdout.strip()
        except Exception:
            return False
    
    def check_health_endpoint(self, service: Service) -> bool:
        """Check if service health endpoint is responding"""
        try:
            url = f"http://localhost:{service.port}{service.health_endpoint}"
            
            if service.health_method == "POST":
                # Phi uses POST with JSON payload
                response = requests.post(
                    url,
                    json={"prompt": "ping", "n_predict": 4},
                    timeout=5
                )
            else:
                # Mixtral and TOVA use GET requests
                response = requests.get(url, timeout=5)
            
            return response.status_code == 200
        except Exception:
            return False
    
    def check_service_status(self, service: Service) -> ServiceStatus:
        """Comprehensive service status check"""
        # Don't check health too frequently
        current_time = time.time()
        if current_time - service.last_health_check < service.health_check_interval:
            return service.status
        
        service.last_health_check = current_time
        
        # Check PID file first
        pid_exists, pid = self.check_pid_file(service)
        if pid_exists:
            service.pid = pid
        
        # Check port usage
        port_in_use = self.check_port_usage(service.port)
        
        # Check health endpoint if port is in use
        health_responding = False
        if port_in_use:
            health_responding = self.check_health_endpoint(service)
        
        # Determine status based on all checks
        if health_responding:
            return ServiceStatus.RUNNING
        elif port_in_use and pid_exists:
            # Process exists but not responding - might be starting up
            return ServiceStatus.STARTING
        elif port_in_use:
            # Port in use but no PID file - might be started manually
            return ServiceStatus.RUNNING
        else:
            return ServiceStatus.STOPPED
    
    def start_log_monitoring(self):
        """Start monitoring log files for all services"""
        for service in self.services.values():
            self.monitor_log_file(service)
    
    def monitor_log_file(self, service: Service):
        """Monitor a log file using tail -f in a separate thread"""
        def tail_log():
            try:
                # Create log file if it doesn't exist
                Path(service.log_file).touch(exist_ok=True)
                
                # Use tail -f to follow the log with proper error handling
                process = subprocess.Popen(
                    ["tail", "-f", "-n", "50", service.log_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                service.log_process = process
                
                while self.running and process.poll() is None:
                    try:
                        line = process.stdout.readline()
                        if line:
                            line = line.strip()
                            if line:  # Skip empty lines
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                formatted_line = f"[{timestamp}] {line}"
                                service.log_buffer.append(formatted_line)
                                
                                # Add to combined logs with service identifier
                                color = {"mixtral": "magenta", "phi": "cyan", "tova": "yellow"}.get(service.name, "white")
                                prefix = {"mixtral": "🎭", "phi": "🔍", "tova": "🎪"}.get(service.name, "●")
                                self.combined_logs.append(f"[{color}]{prefix}[/{color}] {formatted_line}")
                    except Exception as e:
                        # Handle file rotation or other issues
                        if "No such file or directory" in str(e):
                            time.sleep(1)  # Wait for file to be recreated
                            continue
                        break
                    
            except Exception as e:
                service.log_buffer.append(f"[red]Log monitoring error: {e}[/red]")
        
        thread = threading.Thread(target=tail_log, daemon=True)
        thread.start()
    
    def update_service_statuses(self):
        """Update status for all services"""
        for service in self.services.values():
            old_status = service.status
            new_status = self.check_service_status(service)
            
            # Don't override transitional states immediately
            if old_status in [ServiceStatus.STARTING, ServiceStatus.STOPPING]:
                # Give it a moment before checking
                continue
            
            service.status = new_status
    
    async def start_service(self, service_name: str):
        """Start a service with proper health checks and retry logic"""
        service = self.services[service_name]
        
        # Check if script exists
        if not self.check_script_exists(service.start_script):
            console.print(f"[red]✗ Start script not found: {service.start_script}[/red]")
            service.status = ServiceStatus.ERROR
            return
        
        if service.status == ServiceStatus.RUNNING:
            console.print(f"[yellow]⚠ {service.display_name} is already running[/yellow]")
            return
        
        service.status = ServiceStatus.STARTING
        console.print(f"[green]▶ Starting {service.display_name}...[/green]")
        
        try:
            # Run start command
            process = subprocess.Popen(
                ["bash", service.start_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Wait for service to start with exponential backoff
            max_attempts = 10
            for attempt in range(max_attempts):
                await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1, 2, 4, 8, 16...
                
                # Check if it actually started
                service.status = self.check_service_status(service)
                if service.status == ServiceStatus.RUNNING:
                    console.print(f"[green]✓ {service.display_name} started successfully[/green]")
                    return
                elif service.status == ServiceStatus.ERROR:
                    break
            
            # If we get here, service failed to start
            console.print(f"[red]✗ {service.display_name} failed to start after {max_attempts} attempts[/red]")
            service.status = ServiceStatus.ERROR
            
        except Exception as e:
            service.status = ServiceStatus.ERROR
            console.print(f"[red]✗ Failed to start {service_name}: {e}[/red]")
    
    async def stop_service(self, service_name: str):
        """Stop a service with proper cleanup"""
        service = self.services[service_name]
        
        if service.status not in [ServiceStatus.RUNNING, ServiceStatus.STARTING]:
            console.print(f"[yellow]⚠ {service.display_name} is not running[/yellow]")
            return
        
        service.status = ServiceStatus.STOPPING
        console.print(f"[yellow]■ Stopping {service.display_name}...[/yellow]")
        
        try:
            # Try PID file first
            pid_exists, pid = self.check_pid_file(service)
            if pid_exists:
                # Send SIGTERM
                os.kill(pid, signal.SIGTERM)
                await asyncio.sleep(2)
                
                # Check if still running, force kill if needed
                try:
                    os.kill(pid, 0)
                    os.kill(pid, signal.SIGKILL)
                    await asyncio.sleep(1)
                except OSError:
                    pass
                
                # Remove PID file
                Path(service.pid_file).unlink(missing_ok=True)
            else:
                # No PID file, try to kill by port
                try:
                    result = subprocess.run(
                        ["lsof", "-ti", f":{service.port}"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        pids = result.stdout.strip().split('\n')
                        for pid_str in pids:
                            try:
                                pid = int(pid_str)
                                os.kill(pid, signal.SIGTERM)
                            except (ValueError, OSError):
                                pass
                        await asyncio.sleep(2)
                except Exception:
                    pass
            
            service.status = ServiceStatus.STOPPED
            service.pid = None
            console.print(f"[green]✓ {service.display_name} stopped[/green]")
            
        except Exception as e:
            service.status = ServiceStatus.ERROR
            console.print(f"[red]✗ Failed to stop {service_name}: {e}[/red]")
    
    async def restart_service(self, service_name: str):
        """Restart a service"""
        console.print(f"[cyan]🔄 Restarting {self.services[service_name].display_name}...[/cyan]")
        await self.stop_service(service_name)
        await asyncio.sleep(2)
        await self.start_service(service_name)
    
    async def start_all_services(self):
        """Start all services in order with proper delays"""
        console.print("[cyan]🚀 Starting all services...[/cyan]")
        for service_name in ["mixtral", "phi", "tova"]:
            await self.start_service(service_name)
            await asyncio.sleep(3)  # Give each service time to start
    
    async def stop_all_services(self):
        """Stop all services in reverse order"""
        console.print("[cyan]🛑 Stopping all services...[/cyan]")
        for service_name in ["tova", "phi", "mixtral"]:
            await self.stop_service(service_name)
            await asyncio.sleep(2)
    
    def render_status_table(self) -> Table:
        """Render services status table"""
        table = Table(box=box.ROUNDED, expand=True, show_header=True, title="[bold]TOVA v4 Service Status[/bold]")
        table.add_column("#", style="dim", width=3)
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Port", justify="center")
        table.add_column("PID", justify="center")
        
        for idx, (name, service) in enumerate(self.services.items(), 1):
            table.add_row(
                str(idx),
                service.display_name,
                service.status.value,
                str(service.port),
                str(service.pid) if service.pid else "-"
            )
        
        return table
    
    def render_recent_logs(self) -> Panel:
        """Render recent logs"""
        log_lines = list(self.combined_logs)[-10:]  # Last 10 log entries
        
        if not log_lines:
            log_content = "[dim]Waiting for logs...[/dim]"
        else:
            log_content = "\n".join(log_lines)
        
        return Panel(
            log_content,
            title="[bold]Recent Logs[/bold]",
            border_style="blue",
            box=box.ROUNDED
        )
    
    def show_main_menu(self):
        """Show the main menu"""
        console.print("\n[bold magenta]🎪 TOVA v4 Control Center[/bold magenta]")
        console.print(f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n")
        
        # Update service statuses
        self.update_service_statuses()
        
        # Show status table
        console.print(self.render_status_table())
        console.print()
        
        # Show recent logs
        console.print(self.render_recent_logs())
        console.print()
        
        # Show menu options
        console.print("[yellow]Menu Options:[/yellow]")
        console.print("  1-3: Select service by number")
        console.print("  s:   Start selected service")
        console.print("  x:   Stop selected service")
        console.print("  r:   Restart selected service")
        console.print("  a:   Start all services")
        console.print("  k:   Stop all services")
        console.print("  l:   Show recent logs")
        console.print("  q:   Quit")
        console.print()
    
    def run(self):
        """Main menu loop"""
        selected_service = None
        
        while self.running:
            try:
                # Clear screen and show menu
                console.clear()
                self.show_main_menu()
                
                if selected_service is not None:
                    service_name = self.service_list[selected_service - 1]
                    console.print(f"[bold cyan]Selected:[/bold cyan] {self.services[service_name].display_name}")
                    console.print()
                
                # Get user input
                console.print("[yellow]Enter command:[/yellow] ", end="")
                cmd = input().strip().lower()
                
                if cmd == 'q':
                    self.running = False
                elif cmd in ['1', '2', '3']:
                    selected_service = int(cmd)
                    console.print(f"[green]Selected service {selected_service}[/green]")
                elif cmd == 's' and selected_service is not None:
                    service_name = self.service_list[selected_service - 1]
                    asyncio.run(self.start_service(service_name))
                elif cmd == 'x' and selected_service is not None:
                    service_name = self.service_list[selected_service - 1]
                    asyncio.run(self.stop_service(service_name))
                elif cmd == 'r' and selected_service is not None:
                    service_name = self.service_list[selected_service - 1]
                    asyncio.run(self.restart_service(service_name))
                elif cmd == 'a':
                    asyncio.run(self.start_all_services())
                elif cmd == 'k':
                    asyncio.run(self.stop_all_services())
                elif cmd == 'l':
                    # Show more detailed logs
                    console.print("\n[bold]Recent Logs:[/bold]")
                    for log in list(self.combined_logs)[-20:]:
                        console.print(log)
                    input("\nPress Enter to continue...")
                elif cmd:
                    console.print(f"[red]Unknown command: {cmd}[/red]")
                    input("Press Enter to continue...")
                    
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                input("Press Enter to continue...")

async def main():
    """Main entry point"""
    tui = TovaTUIMenu()
    
    try:
        tui.run()
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
    finally:
        console.print("\n[yellow]✨ TOVA TUI shutdown complete[/yellow]")

if __name__ == "__main__":
    asyncio.run(main()) 