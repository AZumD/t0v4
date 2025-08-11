# TOVA_TUI.md

## Purpose
Advanced Terminal User Interface (TUI) for managing TOVA v4 services with real-time monitoring, health checks, and robust error handling.

## Features
- **Service Management**: Start, stop, restart individual services or all at once
- **Real-time Monitoring**: Live log monitoring with color-coded service identification
- **Health Checks**: Comprehensive status checking via PID files, ports, and API endpoints
- **Robust Error Handling**: Graceful handling of service failures, missing files, and network issues
- **Simplified Controls**: Intuitive keyboard navigation and commands
- **Service Dependencies**: Proper startup/shutdown order (mixtral → phi → tova)

## Usage
```bash
# Run the TUI
python scripts/utils/tova_tui.py

# The interface will show service status and live logs
```

## Service Configuration

### Mixtral (Primary Brain)
- **Port**: 8000
- **Script**: `scripts/start/start_mixtral.sh`
- **Health Endpoint**: `/v1/models` (GET)
- **PID File**: `data/logs/mixtral.pid`
- **Log File**: `data/logs/mixtral.log`

### Phi (Background Brain)
- **Port**: 8001
- **Script**: `scripts/start/start_phi.sh`
- **Health Endpoint**: `/completion` (POST)
- **PID File**: `data/logs/phi.pid`
- **Log File**: `data/logs/phi.log`

### TOVA Core
- **Port**: 8002
- **Script**: `scripts/start/start_tova.sh`
- **Health Endpoint**: `/health` (GET)
- **PID File**: `data/logs/tova.pid`
- **Log File**: `data/logs/tova.log`

## Controls

### Navigation
- **K**: Move up (previous service)
- **J**: Move down (next service)

### Service Management
- **S**: Start selected service
- **X**: Stop selected service
- **R**: Restart selected service

### Bulk Operations
- **A**: Start all services (in order: mixtral → phi → tova)
- **K** (capital): Stop all services (in reverse: tova → phi → mixtral)

### System
- **Q**: Quit TUI

## Status Indicators

| Status | Description |
|--------|-------------|
| 🟢 Running | Service is active and responding to health checks |
| 🔴 Stopped | Service is not running |
| 🟡 Starting | Service is in startup process |
| 🟡 Stopping | Service is in shutdown process |
| 🔴 Error | Service encountered an error |

## Health Check System

### Comprehensive Status Detection
1. **PID File Check**: Verifies process ID file exists and contains valid PID
2. **Process Validation**: Confirms process is actually running (not stale PID)
3. **Port Usage**: Checks if service port is in use via `lsof`
4. **API Health**: Tests service-specific health endpoints
5. **Response Validation**: Ensures services are responding correctly

### Health Check Frequency
- Health checks are performed every 5 seconds per service
- Prevents excessive API calls while maintaining responsiveness
- Automatic retry with exponential backoff for startup operations

## Error Recovery

### Service Startup Failures
- **Script Validation**: Checks if start scripts exist and are executable
- **Exponential Backoff**: Retries startup with increasing delays (1, 2, 4, 8, 16... seconds)
- **Maximum Attempts**: Limits retry attempts to prevent infinite loops
- **Clear Error Messages**: Provides specific failure reasons

### Service Shutdown Issues
- **Graceful Termination**: Sends SIGTERM first, then SIGKILL if needed
- **PID File Cleanup**: Removes stale PID files automatically
- **Port-based Killing**: Falls back to killing processes by port if PID file missing
- **Process Validation**: Ensures processes are actually terminated

### Log Monitoring Resilience
- **File Creation**: Automatically creates log files if they don't exist
- **Rotation Handling**: Gracefully handles log file rotation
- **Error Isolation**: Individual log monitoring failures don't affect other services
- **Noise Filtering**: Filters out excessive debug/trace messages

## Log Display Features

### Real-time Monitoring
- **Color-coded Services**: Each service has distinct color and emoji
- **Timestamp Formatting**: Shows relative timestamps for log entries
- **Noise Reduction**: Filters out verbose debug messages
- **Buffer Management**: Maintains last 100 log entries with automatic cleanup

### Service Identification
- 🎭 **Mixtral**: Magenta color, primary brain service
- 🔍 **Phi**: Cyan color, background brain service  
- 🎪 **TOVA**: Yellow color, core application service

## Technical Implementation

### Async Architecture
- **Non-blocking UI**: Uses asyncio for responsive interface
- **Concurrent Operations**: Handles multiple services simultaneously
- **Input Buffering**: Prevents key input lag and buffering issues
- **Graceful Shutdown**: Proper cleanup of all monitoring threads

### Process Management
- **Subprocess Handling**: Proper management of service processes
- **Signal Handling**: Correct SIGTERM/SIGKILL usage
- **Resource Cleanup**: Automatic cleanup of PID files and processes
- **Error Propagation**: Clear error reporting to user

### Network Operations
- **Timeout Protection**: 5-second timeouts for all HTTP requests
- **Endpoint-specific Logic**: Different handling for GET vs POST endpoints
- **Connection Resilience**: Graceful handling of network failures
- **Health Validation**: Service-specific health check implementations

## Dependencies
- `rich`: Terminal UI framework
- `asyncio`: Async programming support
- `requests`: HTTP health check testing
- `subprocess`: Process management
- `pathlib`: File system operations
- `termios`, `tty`: Terminal input handling

## Integration
- **Script Compatibility**: Works with existing start scripts
- **Log Integration**: Monitors actual service log files
- **PID Management**: Respects PID files created by start scripts
- **Health Endpoints**: Uses actual service API endpoints

## Safety Features
- **Non-destructive Testing**: Test script validates functionality safely
- **Process Validation**: Multiple checks before assuming service status
- **Graceful Degradation**: Continues operation even if some services fail
- **Clear Feedback**: Detailed status messages for all operations

## Maintenance
- **Configuration Updates**: Easy to modify service definitions
- **Health Check Customization**: Adjustable health check intervals and endpoints
- **Log Filtering**: Configurable noise reduction rules
- **Error Handling**: Extensible error recovery mechanisms 