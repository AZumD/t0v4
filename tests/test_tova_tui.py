#!/usr/bin/env python3
"""Test script for TOVA TUI functionality"""

import asyncio
import subprocess
import time
import os
import signal
import requests
from pathlib import Path
import sys

class TovaTUITester:
    def __init__(self):
        self.project_root = Path("/home/anthon/t0v4")
        self.log_path = self.project_root / "data" / "logs"
        self.scripts_path = self.project_root / "scripts" / "start"
        
        # Service definitions matching the actual scripts
        self.services = {
            "mixtral": {
                "port": 8000,
                "pid_file": str(self.log_path / "mixtral.pid"),
                "log_file": str(self.log_path / "mixtral.log"),
                "start_script": str(self.scripts_path / "start_mixtral.sh"),
                "health_endpoint": "/v1/models"
            },
            "phi": {
                "port": 8001,
                "pid_file": str(self.log_path / "phi.pid"),
                "log_file": str(self.log_path / "phi.log"),
                "start_script": str(self.scripts_path / "start_phi.sh"),
                "health_endpoint": "/completion"
            },
            "tova": {
                "port": 8002,
                "pid_file": str(self.log_path / "tova.pid"),
                "log_file": str(self.log_path / "tova.log"),
                "start_script": str(self.scripts_path / "start_tova.sh"),
                "health_endpoint": "/health"
            }
        }
        
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f": {message}"
        print(result)
        self.test_results.append((test_name, success, message))
    
    def check_script_exists(self, script_path: str) -> bool:
        """Check if start script exists and is executable"""
        path = Path(script_path)
        exists = path.exists()
        executable = os.access(path, os.X_OK)
        return exists and executable
    
    def check_pid_file(self, pid_file: str) -> tuple[bool, int]:
        """Check if PID file exists and contains valid PID"""
        try:
            if not Path(pid_file).exists():
                return False, 0
            
            with open(pid_file, 'r') as f:
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
    
    def check_health_endpoint(self, service_name: str, port: int, endpoint: str) -> bool:
        """Check if service health endpoint is responding"""
        try:
            url = f"http://localhost:{port}{endpoint}"
            
            if service_name == "phi":
                # Phi uses /completion with POST request
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
    
    def test_script_existence(self):
        """Test 1: Check if all start scripts exist and are executable"""
        print("\n🔍 Testing script existence and permissions...")
        
        for service_name, config in self.services.items():
            script_exists = self.check_script_exists(config["start_script"])
            self.log_test(
                f"Script exists: {service_name}",
                script_exists,
                config["start_script"] if not script_exists else ""
            )
    
    def test_log_directory(self):
        """Test 2: Check if log directory exists and is writable"""
        print("\n📁 Testing log directory...")
        
        log_dir_exists = self.log_path.exists()
        log_dir_writable = os.access(self.log_path, os.W_OK)
        
        self.log_test("Log directory exists", log_dir_exists)
        self.log_test("Log directory writable", log_dir_writable)
    
    def test_current_service_status(self):
        """Test 3: Check current status of all services"""
        print("\n🔍 Testing current service status...")
        
        for service_name, config in self.services.items():
            # Check PID file
            pid_exists, pid = self.check_pid_file(config["pid_file"])
            
            # Check port usage
            port_in_use = self.check_port_usage(config["port"])
            
            # Check health endpoint
            health_responding = False
            if port_in_use:
                health_responding = self.check_health_endpoint(
                    service_name, 
                    config["port"], 
                    config["health_endpoint"]
                )
            
            status = "Running" if health_responding else "Stopped"
            self.log_test(
                f"Service status: {service_name}",
                True,  # Always pass as this is just status check
                f"{status} (PID: {pid if pid else 'N/A'}, Port: {'In Use' if port_in_use else 'Free'})"
            )
    
    def test_service_start_stop(self):
        """Test 4: Test service status detection (skip start/stop if already running)"""
        print("\n🚀 Testing service status detection...")
        
        service_name = "tova"
        config = self.services[service_name]
        
        # Check current status
        pid_exists, pid = self.check_pid_file(config["pid_file"])
        port_in_use = self.check_port_usage(config["port"])
        health_responding = self.check_health_endpoint(
            service_name, 
            config["port"], 
            config["health_endpoint"]
        )
        
        # Determine if service is running
        is_running = port_in_use and health_responding
        
        if is_running:
            # Service is already running, just test status detection
            self.log_test(
                f"Service status detection: {service_name}",
                True,
                f"Already running (PID: {pid if pid else 'N/A'}, Health: {'OK' if health_responding else 'Failed'})"
            )
            
            # Test that we can detect the running service
            self.log_test(
                f"Port detection: {service_name}",
                port_in_use,
                f"Port {config['port']} is {'in use' if port_in_use else 'free'}"
            )
            
            self.log_test(
                f"Health endpoint: {service_name}",
                health_responding,
                f"Health endpoint {config['health_endpoint']} is {'responding' if health_responding else 'not responding'}"
            )
        else:
            # Service is not running, test startup
            print(f"Starting {service_name}...")
            try:
                process = subprocess.Popen(
                    ["bash", config["start_script"]],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                # Wait for service to start
                time.sleep(5)
                
                # Check if started successfully
                pid_exists, pid = self.check_pid_file(config["pid_file"])
                port_in_use = self.check_port_usage(config["port"])
                health_responding = self.check_health_endpoint(
                    service_name, 
                    config["port"], 
                    config["health_endpoint"]
                )
                
                start_success = port_in_use and health_responding
                self.log_test(
                    f"Start service: {service_name}",
                    start_success,
                    f"PID: {pid}, Health: {'OK' if health_responding else 'Failed'}"
                )
                
                if start_success:
                    # Test stopping service
                    print(f"Stopping {service_name}...")
                    try:
                        if pid:
                            os.kill(pid, signal.SIGTERM)
                        else:
                            # Kill by port if no PID
                            result = subprocess.run(
                                ["lsof", "-ti", f":{config['port']}"],
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
                        
                        time.sleep(3)
                        
                        # Check if stopped
                        pid_exists_after, _ = self.check_pid_file(config["pid_file"])
                        port_in_use_after = self.check_port_usage(config["port"])
                        
                        stop_success = not port_in_use_after
                        self.log_test(
                            f"Stop service: {service_name}",
                            stop_success,
                            f"PID file: {'Removed' if not pid_exists_after else 'Still exists'}, Port: {'Free' if not port_in_use_after else 'Still in use'}"
                        )
                        
                    except OSError as e:
                        self.log_test(f"Stop service: {service_name}", False, str(e))
            
            except Exception as e:
                self.log_test(f"Start service: {service_name}", False, str(e))
    
    def test_log_file_creation(self):
        """Test 5: Test log file creation and monitoring"""
        print("\n📝 Testing log file creation...")
        
        for service_name, config in self.services.items():
            log_file = Path(config["log_file"])
            
            # Create log file if it doesn't exist
            log_file.touch(exist_ok=True)
            
            # Check if file is writable
            writable = os.access(log_file, os.W_OK)
            self.log_test(
                f"Log file writable: {service_name}",
                writable,
                str(log_file)
            )
    
    def test_pid_file_management(self):
        """Test 6: Test PID file management"""
        print("\n🆔 Testing PID file management...")
        
        for service_name, config in self.services.items():
            pid_file = Path(config["pid_file"])
            
            # Test creating PID file
            test_pid = 99999  # Invalid PID for testing
            try:
                with open(pid_file, 'w') as f:
                    f.write(str(test_pid))
                
                # Check if file was created
                created = pid_file.exists()
                self.log_test(
                    f"PID file creation: {service_name}",
                    created,
                    str(pid_file)
                )
                
                # Clean up test PID file
                if created:
                    pid_file.unlink()
                
            except Exception as e:
                self.log_test(f"PID file creation: {service_name}", False, str(e))
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 TOVA TUI Test Suite")
        print("=" * 50)
        
        self.test_script_existence()
        self.test_log_directory()
        self.test_current_service_status()
        self.test_service_start_stop()
        self.test_log_file_creation()
        self.test_pid_file_management()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print("❌ Some tests failed. Check the output above.")
            return False

async def main():
    """Main test runner"""
    tester = TovaTUITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ TUI is ready for use!")
        print("Run: python scripts/utils/tova_tui.py")
    else:
        print("\n⚠️  Please fix the failing tests before using the TUI")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 