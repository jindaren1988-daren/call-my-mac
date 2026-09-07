# Mac Companion

Python 3.11+ FastAPI server. Runs on the Mac (or Linux for text demo).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export CALL_MY_MAC_TOKEN=dev-token-change-me
export CALL_MY_MAC_DRY_RUN=1
uvicorn app:app --host 127.0.0.1 --port 8742
```

Listens for Tailscale clients in production (`CALL_MY_MAC_HOST` = Tailscale IP).
Auth: `Authorization: Bearer $CALL_MY_MAC_TOKEN`.

Agent code lives in `../agent` (added to `sys.path` by `app.py`).
