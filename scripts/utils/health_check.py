#!/usr/bin/env python3
import sys, json, urllib.request

def check(host: str, port: int) -> None:
    url = f"http://{host}:{port}/completion"
    req = urllib.request.Request(url, data=json.dumps({"prompt":"ping","n_predict":8}).encode('utf-8'), headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        print(r.read().decode('utf-8'))

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    check(host, port) 