# START_ALL

Script: `scripts/start/start_all.sh`

- Purpose: Start all services in sequence.
- Usage: `bash scripts/start/start_all.sh`
- Notes: Expects llama.cpp servers to expose `GET /v1/models` for health; `/health` is not available on commit 799a1cb1. 