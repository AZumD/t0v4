# OVERVIEW

- Brain backends use llama.cpp servers:
  - Mixtral on `http://localhost:8000` via `scripts/start/start_mixtral.sh`
  - Phi on `http://localhost:8001` via `scripts/start/start_phi.sh`
- Available endpoints (older llama.cpp commit 799a1cb1):
  - `POST /completion` — text generation
  - `GET /v1/models` — liveness/info (used for health checks)
  - `/health` — not available
- Environment knobs:
  - `MIXTRAL_THREADS`, `MIXTRAL_BATCH`, `MIXTRAL_NGL` for server start defaults.
  - `MIXTRAL_STOP_TOKENS` for client stop token CSV override (default `["<|im_end|>", "</s>"]`).
  - `MIXTRAL_STREAM_LOG=1` to enable light streaming metrics in backend logs. 