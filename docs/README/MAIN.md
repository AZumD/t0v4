# MAIN

TOVA v4 system overview and key environment variables.

## Environment Knobs

- Server (Mixtral llama.cpp):
  - `MIXTRAL_THREADS` (default: `$(nproc)`)
  - `MIXTRAL_BATCH` (default: `64`)
  - `MIXTRAL_NGL` (default: `24`)
- Client (Mixtral streaming):
  - `MIXTRAL_STOP_TOKENS` (CSV of stop tokens; default `["<|im_end|>", "</s>"]`)
  - `MIXTRAL_STREAM_LOG=1` (enable light streaming metrics in backend logs) 