# START_MIXTRAL

Script: `scripts/start/start_mixtral.sh`

- Purpose: Launches llama.cpp server for Mixtral using a local `.gguf` model, compatible with older llama.cpp (no `--hf-repo`).
- Behavior: Starts on port `8000`, writes logs to `data/logs/mixtral.log`, and verifies availability via `GET /v1/models`.
- Usage: `bash scripts/start/start_mixtral.sh`
- Notes:
  - Expects model at `data/models/dolphin-2.7-mixtral-8x7b.Q4_K_M.gguf`.
  - Health endpoint `/health` is not available in this llama.cpp version; `/v1/models` is used instead. 