# MAIN

Script: `tova/main.py`

- Purpose: FastAPI app entry point exposing HTTP and WebSocket routes.
- How to run: `uvicorn tova.main:app --reload`
- Key endpoints:
  - `GET /health`: Liveness
  - `POST /api/chat`: Echo placeholder
  - `WS /ws`: Echo broadcast 