# START_MIXTRAL

Script: `scripts/start/start_mixtral.sh`

- Purpose: Launch llama.cpp server for Mixtral using a local `.gguf` model with CUDA offload.
- Behavior: Starts on port `8000`, writes logs to `data/logs/mixtral.log`, and verifies availability via `GET /v1/models`.
- Usage: `bash scripts/start/start_mixtral.sh`
- Defaults (overridable via env):
  - `MIXTRAL_THREADS` → defaults to `$(nproc)`
  - `MIXTRAL_BATCH` → defaults to `64`
  - `MIXTRAL_NGL` → defaults to `24` (RTX 3080 12GB baseline)
  - `MIXTRAL_MODEL_PATH` → explicit path to `.gguf` (takes precedence)
- Model resolution order:
  1. `MIXTRAL_MODEL_PATH` if set and exists
  2. `/home/anthon/llm/models/mixtral/dolphin-2.7-mixtral-8x7b.Q4_K_M.gguf`
  3. First match in `~/.cache/llama.cpp/*dolphin-2.7-mixtral-8x7b.Q4_K_M.gguf`

Notes:
- We do not store models in the repo; `.gitignore` excludes `tova_v4/data/models/**`.
- Ensure the model exists in one of the external locations or set `MIXTRAL_MODEL_PATH`. 