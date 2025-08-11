#!/usr/bin/env python3
"""TOVA v4 Terminal User Interface - System Management & Monitoring"""

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
import select
import termios
import tty

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich.align import Align
    from rich import box
except ImportError:
    print("Installing required package: rich")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich"]) 
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
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
    start_command: List[str]
    status: ServiceStatus = ServiceStatus.STOPPED
    pid: Optional[int] = None
    log_process: Optional[subprocess.Popen] = None
    log_buffer: deque = None
    
    def __post_init__(self):
        if self.log_buffer is None:
            self.log_buffer = deque(maxlen=100)

class TovaTUI:
    def __init__(self):
        self.project_root = Path("/home/anthon/t0v4/tova_v4")
        self.log_path = self.project_root / "data" / "logs"
        self.scripts_path = self.project_root / "scripts" / "start"
        
        # Ensure log directory exists
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        # Define services including main.py
        self.services: Dict[str, Service] = {
            "mixtral": Service(
                name="mixtral",
                display_name="🎭 Mixtral (Primary Brain)",
                port=8000,
                pid_file=str(self.log_path / "mixtral.pid"),
                log_file=str(self.log_path / "mixtral.log"),
                start_command=["bash", str(self.scripts_path / "start_mixtral.sh")]
            ),
            "phi": Service(
                name="phi",
                display_name="🔍 Phi (Background Brain)",
                port=8001,
                pid_file=str(self.log_path / "phi.pid"),
                log_file=str(self.log_path / "phi.log"),
                start_command=["bash", str(self.scripts_path / "start_phi.sh")]
            ),
            "tova": Service(
                name="tova",
                display_name="🎪 TOVA Core (main.py)",
                port=8002,
                pid_file=str(self.log_path / "tova.pid"),
                log_file=str(self.log_path / "tova.log"),
                start_command=["bash", str(self.scripts_path / "start_tova.sh")]
            )
        }
        
        self.selected_service = 0
        self.service_list = list(self.services.keys())
        self.log_tail_lines = 30
        self.running = True
        self.layout = Layout()
        self.combined_logs = deque(maxlen=100)
        self.key_buffer = []
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
    
    def check_service_status(self, service: Service) -> ServiceStatus:
        """Check if a service is running via PID file or process check"""
        try:
            # First check PID file
            if Path(service.pid_file).exists():
                with open(service.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                    # Check if process is running
                    os.kill(pid, 0)  # Signal 0 just checks if process exists
                    service.pid = pid
                    return ServiceStatus.RUNNING
        except (OSError, ValueError, FileNotFoundError):
            pass
        
        # Also check if service is actually running on its port
        try:
            result = subprocess.run(
                ["lsof", "-i", f":{service.port}"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0 and result.stdout:
                return ServiceStatus.RUNNING
        except:
            pass
        
        service.pid = None
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
                
                # Use tail -f to follow the log
                process = subprocess.Popen(
                    ["tail", "-f", "-n", "50", service.log_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                service.log_process = process
                
                while self.running and process.poll() is None:
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
        """Start a service"""
        service = self.services[service_name]
        if service.status == ServiceStatus.RUNNING:
            self.combined_logs.append(f"[yellow]⚠ {service.display_name} is already running[/yellow]")
            return
        
        service.status = ServiceStatus.STARTING
        self.combined_logs.append(f"[green]▶ Starting {service.display_name}...[/green]")
        
        try:
            # Run start command
            process = subprocess.Popen(
                service.start_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Wait a bit for service to start
            await asyncio.sleep(3)
            
            # Check if it actually started
            service.status = self.check_service_status(service)
            if service.status == ServiceStatus.RUNNING:
                self.combined_logs.append(f"[green]✓ {service.display_name} started successfully[/green]")
            else:
                self.combined_logs.append(f"[red]✗ {service.display_name} failed to start[/red]")
                service.status = ServiceStatus.STOPPED
            
        except Exception as e:
            service.status = ServiceStatus.ERROR
            self.combined_logs.append(f"[red]✗ Failed to start {service_name}: {e}[/red]")
    
    async def stop_service(self, service_name: str):
        """Stop a service"""
        service = self.services[service_name]
        if service.status != ServiceStatus.RUNNING:
            self.combined_logs.append(f"[yellow]⚠ {service.display_name} is not running[/yellow]")
            return
        
        service.status = ServiceStatus.STOPPING
        self.combined_logs.append(f"[yellow]■ Stopping {service.display_name}...[/yellow]")
        
        try:
            if service.pid:
                # Send SIGTERM
                os.kill(service.pid, signal.SIGTERM)
                await asyncio.sleep(1)
                
                # Check if still running, force kill if needed
                try:
                    os.kill(service.pid, 0)
                    os.kill(service.pid, signal.SIGKILL)
                    await asyncio.sleep(0.5)
                except OSError:
                    pass
                
                # Remove PID file
                Path(service.pid_file).unlink(missing_ok=True)
            
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
        await asyncio.sleep(1)
        await self.start_service(service_name)
    
    async def start_all_services(self):
        """Start all services in order"""
        self.combined_logs.append("[cyan]🚀 Starting all services...[/cyan]")
        for service_name in ["mixtral", "phi", "tova"]:
            await self.start_service(service_name)
            await asyncio.sleep(2)
    
    async def stop_all_services(self):
        """Stop all services in reverse order"""
        self.combined_logs.append("[cyan]🛑 Stopping all services...[/cyan]")
        for service_name in ["tova", "phi", "mixtral"]:
            await self.stop_service(service_name)
            await asyncio.sleep(1)
    
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
            
            table.add_row(
                prefix,
                Text(service.display_name, style=style),
                service.status.value,
                str(service.port),
                str(service.pid) if service.pid else "-"
            )
        
        return Panel(table, title="[bold]Service Management[/bold]", 
                    border_style="green", box=box.ROUNDED)
    
    def render_logs(self) -> Panel:
        """Render combined logs panel"""
        # Get last N log lines
        log_lines = list(self.combined_logs)[-self.log_tail_lines:]
        
        if not log_lines:
            log_lines = ["[dim]Waiting for logs...[/dim]"]
        
        log_content = "\n".join(log_lines)
        
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
            "[dim]Navigation: ↑/↓ or J/K to select service[/dim]"
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
    
    async def handle_input(self):
        """Handle keyboard input in async way"""
        stdin_fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(stdin_fd)
        
        try:
            tty.setraw(stdin_fd)
            
            while self.running:
                # Check if input is available
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key = sys.stdin.read(1)
                    
                    if key == 'q' or key == 'Q':
                        self.running = False
                    elif key == '\x1b':  # ESC sequence for arrow keys
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            next_char = sys.stdin.read(1)
                            if next_char == '[':
                                if select.select([sys.stdin], [], [], 0.1)[0]:
                                    arrow = sys.stdin.read(1)
                                    if arrow == 'A':  # Up arrow
                                        self.selected_service = max(0, self.selected_service - 1)
                                    elif arrow == 'B':  # Down arrow
                                        self.selected_service = min(len(self.services) - 1, 
                                                                   self.selected_service + 1)
                    elif key == 'k' or key == 'K':  # vim-style up
                        self.selected_service = max(0, self.selected_service - 1)
                    elif key == 'j' or key == 'J':  # vim-style down
                        self.selected_service = min(len(self.services) - 1, 
                                                   self.selected_service + 1)
                    elif key == 's' or key == 'S':
                        service_name = self.service_list[self.selected_service]
                        await self.start_service(service_name)
                    elif key == 'x' or key == 'X':
                        service_name = self.service_list[self.selected_service]
                        await self.stop_service(service_name)
                    elif key == 'r' or key == 'R':
                        service_name = self.service_list[self.selected_service]
                        await self.restart_service(service_name)
                    elif key == 'a' or key == 'A':
                        await self.start_all_services()
                    elif key.lower() == 'k' and key.isupper():  # Capital K for kill all
                        await self.stop_all_services()
                
                await asyncio.sleep(0.05)
                
        finally:
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)
    
    async def run(self):
        """Main TUI loop"""
        # Start input handler
        input_task = asyncio.create_task(self.handle_input())
        
        with Live(self.render(), refresh_per_second=2, console=console, screen=True) as live:
            try:
                while self.running:
                    live.update(self.render())
                    await asyncio.sleep(0.5)
            except KeyboardInterrupt:
                self.running = False
        
        # Clean up
        input_task.cancel()
        try:
            await input_task
        except asyncio.CancelledError:
            pass
        
        # Stop log monitoring
        for service in self.services.values():
            if service.log_process:
                service.log_process.terminate()

async def main():
    """Main entry point"""
    tui = TovaTUI()
    
    try:
        await tui.run()
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
    finally:
        console.print("\n[yellow]✨ TOVA TUI shutdown complete[/yellow]")

if __name__ == "__main__":
    asyncio.run(main())
