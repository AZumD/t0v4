#!/usr/bin/env python3
"""TOVA v4 Simple TUI - Uses console.input() for better compatibility"""

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
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich.align import Align
    from rich import box
    from rich.prompt import Prompt
except ImportError:
    print("Installing required package: rich")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich"])  # nosec - CLI utility install
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich.align import Align
    from rich import box
    from rich.prompt import Prompt

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

class TovaTUISimple:
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
        
        self.selected_service = 0
        self.service_list = list(self.services.keys())
        self.log_tail_lines = 30
        self.running = True
        self.layout = Layout()
        self.combined_logs = deque(maxlen=100)
        self.setup_layout()
        self.start_log_monitoring()
        
    def setup_layout(self):
        """Setup the TUI layout"""
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=4)
        )
        
        self.layout["main"].split_row(
            Layout(name="services", ratio=1),
            Layout(name="logs", ratio=2)
        )
    
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
            self.combined_logs.append(f"[red]✗ Start script not found: {service.start_script}[/red]")
            service.status = ServiceStatus.ERROR
            return
        
        if service.status == ServiceStatus.RUNNING:
            self.combined_logs.append(f"[yellow]⚠ {service.display_name} is already running[/yellow]")
            return
        
        service.status = ServiceStatus.STARTING
        self.combined_logs.append(f"[green]▶ Starting {service.display_name}...[/green]")
        
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
                    self.combined_logs.append(f"[green]✓ {service.display_name} started successfully[/green]")
                    return
                elif service.status == ServiceStatus.ERROR:
                    break
            
            # If we get here, service failed to start
            self.combined_logs.append(f"[red]✗ {service.display_name} failed to start after {max_attempts} attempts[/red]")
            service.status = ServiceStatus.ERROR
            
        except Exception as e:
            service.status = ServiceStatus.ERROR
            self.combined_logs.append(f"[red]✗ Failed to start {service_name}: {e}[/red]")
    
    async def stop_service(self, service_name: str):
        """Stop a service with proper cleanup"""
        service = self.services[service_name]
        
        if service.status not in [ServiceStatus.RUNNING, ServiceStatus.STARTING]:
            self.combined_logs.append(f"[yellow]⚠ {service.display_name} is not running[/yellow]")
            return
        
        service.status = ServiceStatus.STOPPING
        self.combined_logs.append(f"[yellow]■ Stopping {service.display_name}...[/yellow]")
        
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
            self.combined_logs.append(f"[green]✓ {service.display_name} stopped[/green]")
            
        except Exception as e:
            service.status = ServiceStatus.ERROR
            self.combined_logs.append(f"[red]✗ Failed to stop {service_name}: {e}[/red]")
    
    async def restart_service(self, service_name: str):
        """Restart a service"""
        self.combined_logs.append(f"[cyan]🔄 Restarting {self.services[service_name].display_name}...[/cyan]")
        await self.stop_service(service_name)
        await asyncio.sleep(2)
        await self.start_service(service_name)
    
    async def start_all_services(self):
        """Start all services in order with proper delays"""
        self.combined_logs.append("[cyan]🚀 Starting all services...[/cyan]")
        for service_name in ["mixtral", "phi", "tova"]:
            await self.start_service(service_name)
            await asyncio.sleep(3)  # Give each service time to start
    
    async def stop_all_services(self):
        """Stop all services in reverse order"""
        self.combined_logs.append("[cyan]🛑 Stopping all services...[/cyan]")
        for service_name in ["tova", "phi", "mixtral"]:
            await self.stop_service(service_name)
            await asyncio.sleep(2)
    
    def render_header(self) -> Panel:
        """Render the header"""
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row(
            "[bold magenta]🎪 TOVA v4 Control Center[/bold magenta]"
        )
        grid.add_row(
            f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
        )
        return Panel(grid, style="cyan", box=box.DOUBLE)
    
    def render_services(self) -> Panel:
        """Render services panel"""
        table = Table(box=box.ROUNDED, expand=True, show_header=True)
        table.add_column("", style="dim", width=3)
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Port", justify="center")
        table.add_column("PID", justify="center")
        
        for idx, (name, service) in enumerate(self.services.items()):
            # Highlight selected service
            prefix = "→ " if idx == self.selected_service else "  "
            style = "bold yellow" if idx == self.selected_service else ""
            
            # Get PID for display
            pid_display = str(service.pid) if service.pid else "-"
            
            table.add_row(
                prefix,
                Text(service.display_name, style=style),
                service.status.value,
                str(service.port),
                pid_display
            )
        
        return Panel(table, title="[bold]Service Management[/bold]", 
                    border_style="green", box=box.ROUNDED)
    
    def render_logs(self) -> Panel:
        """Render combined logs panel with better formatting"""
        # Get last N log lines and filter noise
        log_lines = list(self.combined_logs)[-self.log_tail_lines:]
        
        if not log_lines:
            log_lines = ["[dim]Waiting for logs...[/dim]"]
        
        # Filter out excessive noise and format timestamps
        filtered_lines = []
        for line in log_lines:
            # Skip very verbose lines
            if any(noise in line.lower() for noise in ["debug", "trace", "verbose"]):
                continue
            filtered_lines.append(line)
        
        log_content = "\n".join(filtered_lines[-20:])  # Show last 20 filtered lines
        
        return Panel(
            log_content,
            title="[bold]Live Combined Logs[/bold] [dim](all services)[/dim]",
            border_style="blue",
            box=box.ROUNDED,
            padding=(0, 1)
        )
    
    def render_footer(self) -> Panel:
        """Render footer with controls"""
        selected_service = self.services[self.service_list[self.selected_service]]
        
        controls = Table.grid(expand=True)
        controls.add_column(ratio=1)
        controls.add_row(
            f"[bold cyan]Selected:[/bold cyan] {selected_service.display_name} | "
            f"[bold]Status:[/bold] {selected_service.status.value}"
        )
        controls.add_row("")
        controls.add_row(
            "[yellow]Controls:[/yellow] "
            "[green]S[/green]:Start  [red]X[/red]:Stop  [cyan]R[/cyan]:Restart  "
            "[green]A[/green]:Start All  [red]K[/red]:Stop All  [magenta]Q[/magenta]:Quit"
        )
        controls.add_row(
            "[dim]Navigation: J/K to select service[/dim]"
        )
        
        return Panel(controls, style="dim", box=box.HEAVY)
    
    def render(self) -> Layout:
        """Render the complete UI"""
        self.update_service_statuses()
        
        self.layout["header"].update(self.render_header())
        self.layout["services"].update(self.render_services())
        self.layout["logs"].update(self.render_logs())
        self.layout["footer"].update(self.render_footer())
        
        return self.layout
    
    def show_menu(self):
        """Show the main menu and handle user input"""
        while self.running:
            # Clear screen and show current status
            console.clear()
            console.print(self.render())
            
            # Show command prompt
            console.print("\n[yellow]Enter command (j/k/s/x/r/a/kk/q):[/yellow] ", end="")
            
            try:
                cmd = input().strip().lower()
                
                if cmd == 'q':
                    self.running = False
                elif cmd == 'k':
                    self.selected_service = max(0, self.selected_service - 1)
                elif cmd == 'j':
                    self.selected_service = min(len(self.services) - 1, 
                                               self.selected_service + 1)
                elif cmd == 's':
                    service_name = self.service_list[self.selected_service]
                    asyncio.run(self.start_service(service_name))
                elif cmd == 'x':
                    service_name = self.service_list[self.selected_service]
                    asyncio.run(self.stop_service(service_name))
                elif cmd == 'r':
                    service_name = self.service_list[self.selected_service]
                    asyncio.run(self.restart_service(service_name))
                elif cmd == 'a':
                    asyncio.run(self.start_all_services())
                elif cmd == 'kk':
                    asyncio.run(self.stop_all_services())
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
    tui = TovaTUISimple()
    
    try:
        tui.show_menu()
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
    finally:
        console.print("\n[yellow]✨ TOVA TUI shutdown complete[/yellow]")

if __name__ == "__main__":
    asyncio.run(main()) 