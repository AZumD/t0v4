### TOVA v4 Mixtral + llama.cpp Diagnostic Report

Date: 2025-08-09
Author: System Investigation

---

## Executive Summary
- The Mixtral GGUF models fail to load in the current `llama.cpp` build with error: `missing tensor 'blk.0.ffn_down_exps.weight'`.
- This occurs for both `dolphin-2.7-mixtral-8x7b.Q4_K_M.gguf` and `mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf` despite correct file sizes and multiple attempts.
- Phi 3.5 Mini GGUF loads and serves correctly, indicating the server and environment are functional.
- Most likely root cause: GGUF tensor naming/version mismatch for Mixtral MoE between our models and the current `llama.cpp` loader. Less likely: corrupted model files (re-download did not resolve), build flags, or resource constraints.

---

## Environment Snapshot
- Host: Linux x86_64 (Arch)
- llama.cpp: build 6006, commit 7f975995, compiled via CMake (CPU-only)
- Start scripts:
  - `tova_v4/scripts/start/start_mixtral.sh` → uses local GGUF on port 8000
  - `tova_v4/scripts/start/start_phi.sh` → Phi on port 8001 (works)
- Models present (`tova_v4/data/models/`):
  - `dolphin-2.7-mixtral-8x7b.Q4_K_M.gguf` (26.44 GB)
  - `mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf` (26.44 GB)

---

## Observations and Evidence

### 1) Mixtral GGUF fails to load
- Repeated server logs:
  - `llama_model_load: error loading model: missing tensor 'blk.0.ffn_down_exps.weight'`
  - Affects both Dolphin Mixtral and Mistral Instruct v0.1 GGUF files.
  - Happens immediately after metadata is parsed; loader cannot find a tensor it expects.
- Model metadata (excerpt) shows MoE parameters:
  - `llama.expert_count = 8`, `llama.expert_used_count = 2`
  - Chat template present; GGUF V3; quantization_version = 2
- Re-downloading the Dolphin model did not change behavior.
- Rebuilding `llama.cpp` from HEAD (7f975995) did not change behavior.

### 2) Phi model loads fine
- `Phi-3.5-mini-instruct-Q4_K_M.gguf` starts and serves normally on port 8001.
- Confirms `llama.cpp` binary and HTTP server functionality.

### 3) Networking/ports
- Port conflicts were encountered only when manually starting extra servers. Not related to the load error.

### 4) Client integration fixes applied
- `MixtralClient` now uses `n_predict` and ChatML wrapping for Dolphin/Mixtral; prompt stitcher now separates system/user.
- These API-side changes are correct but cannot be validated end-to-end until the model loads.

---

## Hypotheses (ranked)

### H1: GGUF tensor naming/version mismatch for Mixtral MoE (Most likely)
- The loader expects MoE tensors named with `...ffn_down_exps...`.
- Our GGUF files may use the older/newer naming convention (e.g., `...ffn_down_experts...`) or a different MoE packing.
- GGUF and Mixtral MoE support evolved over time in `llama.cpp`. Different exporter versions produced incompatible tensor names.
- Evidence: exact, consistent missing tensor name across two different Mixtral GGUFs; re-download + rebuild did not help.

### H2: Out-of-date or incompatible GGUF conversions (Very likely)
- The two GGUF files are from late 2023 / early 2024. Current `llama.cpp` (6006) may expect newer MoE field names than present in those files.
- Fix is to download a GGUF converted with a matching, recent `llama.cpp` exporter that aligns with current tensor naming.

### H3: Model file corruption (Less likely)
- Files are complete in size; repeated download still fails with the same tensor missing.
- Corruption typically yields IO or checksum errors rather than a consistent, specific missing tensor symbol.

### H4: Build flags or CPU/GPU differences (Unlikely)
- GPU warnings are expected (CPU-only build) and unrelated to tensor lookup.
- Phi loads fine with the same build, so base build is healthy.

### H5: Insufficient memory (Unlikely for this error)
- Memory issues commonly cause OOM or allocation failures during tensor mapping, not “missing tensor” errors.

---

## Recommended Next Steps

### A) Fetch a known-good, up-to-date Mixtral GGUF compatible with current llama.cpp
- Prefer official or recently reconverted repos:
  - mistralai/Mixtral-8x7B-Instruct-v0.1-GGUF
  - bartowski/Mixtral-8x7B-Instruct-v0.1-GGUF
  - TheBloke (but ensure files were recently reconverted; older ones may not match)
- Easiest path: let llama.cpp fetch the model via HF integration so versions match:

```bash
# Example: auto-download via llama.cpp server (adjust quant if needed)
/home/anthon/llama.cpp/build/bin/llama-server \
  --hf-repo mistralai/Mixtral-8x7B-Instruct-v0.1:q4_k_m \
  --host 0.0.0.0 --port 8000 --ctx-size 4096 --n-gpu-layers 0 --threads 8 --no-mmap
```

- If this loads, update `start_mixtral.sh` to use `--hf-repo` instead of a local `--model` path.

### B) If A fails, try a different recent quant (Q4_0, Q5_K_M) from the same repo date
- Stay within the same, up-to-date repo to keep exporter alignment.

### C) As a fallback, align llama.cpp to an older tag compatible with our current GGUF files
- If we must keep the existing GGUFs, pin `llama.cpp` to a commit contemporary with the GGUF conversion date (Dec 2023–Jan 2024).
- Process:
  1) Identify a tag near the GGUF conversion window.
  2) `git checkout <tag>` and rebuild with CMake.
  3) Test model loading again.
- Note: pinning older code returns us to a known-compatibility matrix but sacrifices recent fixes.

### D) Validate end-to-end once loading succeeds
- Test `/v1/models` and `/completion`:

```bash
curl http://localhost:8000/v1/models

curl -X POST http://localhost:8000/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\nHello<|im_end|>\n<|im_start|>assistant",
    "n_predict": 64,
    "temperature": 0.7,
    "stream": false
  }'
```

- Then test TOVA (now using `n_predict` and ChatML via `MixtralClient`).

---

## Optional Notes
- Unrelated: `tova_v4/scripts/start/start_phi.sh` currently contains a stray non-shell line at the top. It may break the script depending on how it’s invoked. Consider removing any non-bash content before `#!/bin/bash`.

---

## Conclusion
- The consistent missing tensor strongly indicates a GGUF compatibility mismatch for Mixtral MoE between our files and the current `llama.cpp` loader.
- The most reliable fix is to use a recently converted Mixtral GGUF (preferably via `--hf-repo` with the current `llama.cpp`), or pin `llama.cpp` to an older commit that matches the GGUF conversion.
- Once the model loads, our client-side fixes (ChatML + `n_predict`) position TOVA v4 for correct interaction with `/completion`.

---

## One-line Summary
Mixtral fails to load due to a GGUF MoE naming/version mismatch; resolve by using a recently converted Mixtral GGUF via `--hf-repo` or by pinning `llama.cpp` to a compatible older tag.

## log.txt update
[2025-08-09] Baclaude investigated Mixtral + llama.cpp load failures; identified GGUF MoE tensor naming/version mismatch. Recommended using `--hf-repo` to fetch an updated Mixtral GGUF or pinning llama.cpp to a compatible tag. See report.md. 