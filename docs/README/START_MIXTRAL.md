# START_MIXTRAL

Script: `scripts/start/start_mixtral.sh`

- Purpose: Launch llama.cpp server for Mixtral using a local `.gguf` model with CUDA offload.
- Behavior: Starts on port `8000`, writes logs to `data/logs/mixtral.log`, and verifies availability via `GET /v1/models`.
- Usage: `bash scripts/start/start_mixtral.sh`
- Defaults (overridable via env):
  - `MIXTRAL_THREADS` → defaults to `$(nproc)`
  - `MIXTRAL_BATCH` → defaults to `64`
  - `MIXTRAL_NGL` → defaults to `24` (RTX 3080 12GB baseline)
- Retry: If the server fails to start, the script retries by decrementing `--n-gpu-layers` by 2 until ~14.
- Notes:
  - Expects model at `data/models/dolphin-2.7-mixtral-8x7b.Q4_K_M.gguf`.
  - Health endpoint `/health` is not available in this llama.cpp version; `/v1/models` is used instead. 