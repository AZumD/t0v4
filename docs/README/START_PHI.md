# START_PHI

Script: `scripts/start/start_phi.sh`

- Purpose: Launches llama.cpp server for Phi model on port `8001` using local `.gguf` model.
- Behavior: Writes logs to `data/logs/phi.log`, and verifies availability via `GET /v1/models`.
- Usage: `bash scripts/start/start_phi.sh`
- Notes:
  - Expects model at `/home/anthon/llama.cpp/models/Phi-3.5-mini-instruct-Q4_K_M.gguf` (adjust in script if needed).
  - Health endpoint `/health` is not available in this llama.cpp version; `/v1/models` is used instead. 