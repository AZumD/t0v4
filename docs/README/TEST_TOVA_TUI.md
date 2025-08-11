# TEST_TOVA_TUI.md

## Purpose
Comprehensive test suite for the TOVA TUI (Terminal User Interface) to verify all service management functionality works correctly before deployment.

## Features
- **Script Validation**: Verifies all start scripts exist and are executable
- **Service Status Checking**: Tests PID file management and port usage detection
- **Health Endpoint Testing**: Validates service health endpoints are responding
- **Start/Stop Testing**: Safely tests service lifecycle management
- **Log File Management**: Ensures log files can be created and monitored
- **Error Recovery**: Tests graceful handling of various failure scenarios

## Usage
```bash
# Run the complete test suite
python test/test_tova_tui.py

# Test will output detailed results for each component
```

## Test Coverage

### 1. Script Existence & Permissions
- Verifies `start_mixtral.sh`, `start_phi.sh`, `start_tova.sh` exist
- Checks scripts are executable
- Validates script paths match actual project structure

### 2. Log Directory Management
- Ensures `/home/anthon/t0v4/data/logs/` exists
- Verifies directory is writable
- Tests log file creation capabilities

### 3. Service Status Detection
- PID file existence and validity checking
- Process running verification (not just file existence)
- Port usage detection via `lsof`
- Health endpoint response validation

### 4. Service Lifecycle Testing
- Safe start/stop testing (TOVA only to avoid disrupting running services)
- PID file cleanup verification
- Port release confirmation
- Health check integration

### 5. Log File Operations
- Log file creation testing
- Write permission verification
- File monitoring readiness

### 6. PID File Management
- PID file creation/deletion testing
- Stale PID file detection
- Process validation integration

## Service Endpoints Tested

| Service | Port | Health Endpoint | Method |
|---------|------|-----------------|--------|
| Mixtral | 8000 | `/v1/models` | GET |
| Phi | 8001 | `/completion` | POST |
| TOVA | 8002 | `/health` | GET |

## Safety Features
- **Non-destructive**: Only tests TOVA service start/stop to avoid disrupting running services
- **Graceful cleanup**: Removes test PID files and stops test processes
- **Timeout protection**: All network requests have 5-second timeouts
- **Error isolation**: Individual test failures don't stop the entire suite

## Output Format
```
🧪 TOVA TUI Test Suite
==================================================
🔍 Testing script existence and permissions...
✅ PASS Script exists: mixtral
✅ PASS Script exists: phi
✅ PASS Script exists: tova

📁 Testing log directory...
✅ PASS Log directory exists
✅ PASS Log directory writable

🔍 Testing current service status...
✅ PASS Service status: mixtral: Stopped (PID: N/A, Port: Free)
✅ PASS Service status: phi: Stopped (PID: N/A, Port: Free)
✅ PASS Service status: tova: Running (PID: 12345, Port: In Use)

==================================================
📊 Test Summary
==================================================
Total tests: 15
Passed: 15
Failed: 0
🎉 All tests passed!

✅ TUI is ready for use!
Run: python scripts/utils/tova_tui.py
```

## Dependencies
- `asyncio`: Async test execution
- `subprocess`: Process management testing
- `requests`: HTTP health check testing
- `pathlib`: File system operations
- `os`, `signal`: Process and signal handling

## Integration
- Runs before TUI deployment to ensure all components work
- Validates against actual project structure and scripts
- Provides clear feedback for troubleshooting
- Maintains test results for debugging

## Error Handling
- Graceful handling of missing files/scripts
- Network timeout protection
- Process cleanup on failures
- Clear error messages for each failure point

## Maintenance
- Update service definitions if scripts change
- Modify health endpoints if API changes
- Adjust timeouts based on system performance
- Add new tests for additional TUI features 