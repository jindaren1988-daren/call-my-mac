"""Companion configuration from environment."""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass


@dataclass
class Settings:
    token: str
    dry_run: bool
    host: str
    port: int
    version: str = "0.1.0"


def load_settings() -> Settings:
    token = os.environ.get("CALL_MY_MAC_TOKEN") or secrets.token_urlsafe(24)
    dry = os.environ.get("CALL_MY_MAC_DRY_RUN", "1") != "0"
    host = os.environ.get("CALL_MY_MAC_HOST", "127.0.0.1")
    port = int(os.environ.get("CALL_MY_MAC_PORT", "8742"))
    return Settings(token=token, dry_run=dry, host=host, port=port)
