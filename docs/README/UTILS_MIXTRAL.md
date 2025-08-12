# TOVA Utilities: Kill All Services

Script: `scripts/utils/kill_all.sh`

- Purpose: Terminates all TOVA-related services (Mixtral llama.cpp server, Phi llama-server, TOVA FastAPI).
- Behavior:
  - Invokes `scripts/start/stop_all.sh` to stop services by PID files.
  - Extra safety: uses `pkill -f` for known command signatures.
  - Kills any `llama-server` instances (allowed, as TOVA is the only user).
  - Cleans up stale PID files in `tova_v4/data/logs/`.
- Usage:
  - Run directly: `bash scripts/utils/kill_all.sh`
  - Alias (added to `~/.bashrc`): `tovakill`

Notes:
- Safe to run even if services are not running; it will simply clean stale PID files. 