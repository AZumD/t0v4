"""Basic smoke test for the FastAPI app.

Run with: ./mistralvenv/bin/python test/smoke_test.py
"""
from fastapi.testclient import TestClient

from tova.main import app


def main() -> None:
    client = TestClient(app)

    r = client.get("/health")
    assert r.status_code == 200, r.text
    assert r.json().get("status") == "ok"

    r = client.post("/api/chat", json={"message": "hi"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("received") == "hi"

    print("Smoke tests passed.")


if __name__ == "__main__":
    main() 