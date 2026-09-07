"""Allowlisted Mac capability stubs. Fail closed. Never eval model shell.

Phase 0: always propose commands; live Darwin execution is gated and optional.
Default dry_run=True means we never call system binaries from this process.
"""
from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from typing import Any, Callable


ALLOWED_APPS = {
    "safari": "Safari",
    "finder": "Finder",
    "notes": "Notes",
    "terminal": "Terminal",
    "music": "Music",
    "calendar": "Calendar",
    "mail": "Mail",
    "messages": "Messages",
    "system settings": "System Settings",
    "系统设置": "System Settings",
}

CONFIRM_INTENTS = {"screenshot"}


@dataclass
class CapabilityResult:
    ok: bool
    detail: str
    proposed_cmd: str
    executed: bool = False


def _is_macos() -> bool:
    return platform.system() == "Darwin"


def _allow_live() -> bool:
    """Live execution only when explicitly enabled AND running on macOS."""
    if os.environ.get("CALL_MY_MAC_ALLOW_LIVE", "0") != "1":
        return False
    return _is_macos()


def resolve_app(name: str) -> str:
    key = name.strip().lower()
    app = ALLOWED_APPS.get(key)
    if app:
        return app
    for v in ALLOWED_APPS.values():
        if v.lower() == key:
            return v
    raise ValueError(f"app not allowlisted: {name}")


def execute_capability(
    intent: str,
    args: dict[str, Any],
    *,
    dry_run: bool = True,
) -> CapabilityResult:
    """Resolve intent through allowlist. dry_run never touches the OS."""
    builders: dict[str, Callable[[], CapabilityResult]] = {
        "open_app": lambda: _open_app(args.get("name", ""), dry_run=dry_run),
        "say": lambda: _say(str(args.get("text", "")), dry_run=dry_run),
        "get_battery": lambda: _battery(dry_run=dry_run),
        "screenshot": lambda: _screenshot(args.get("path"), dry_run=dry_run),
        "noop": lambda: CapabilityResult(True, "noop", "noop", executed=False),
    }
    builder = builders.get(intent)
    if builder is None:
        return CapabilityResult(False, f"intent_forbidden:{intent}", "", executed=False)
    try:
        return builder()
    except ValueError as e:
        return CapabilityResult(False, str(e), "", executed=False)
    except Exception as e:  # noqa: BLE001
        return CapabilityResult(False, f"error:{e}", "", executed=False)


def _open_app(name: str, *, dry_run: bool) -> CapabilityResult:
    app = resolve_app(name)
    proposed = f"mac.activate_app name={app}"
    if dry_run or not _allow_live():
        suffix = "" if _is_macos() else " (non-macOS stub)"
        return CapabilityResult(True, f"would activate {app}{suffix}", proposed, executed=False)
    # Live path: deferred to mac/live_runner.py on a real Mac (see README).
    return CapabilityResult(
        True,
        f"live runner not bundled in scaffold; proposed {proposed}",
        proposed,
        executed=False,
    )


def _say(text: str, *, dry_run: bool) -> CapabilityResult:
    if not text.strip():
        return CapabilityResult(False, "empty say text", "mac.say", executed=False)
    safe = text[:200]
    proposed = f"mac.say text={safe!r}"
    if dry_run or not _allow_live():
        return CapabilityResult(True, f"would speak: {safe[:80]}", proposed, executed=False)
    return CapabilityResult(
        True, f"live runner not bundled; proposed {proposed}", proposed, executed=False
    )


def _battery(*, dry_run: bool) -> CapabilityResult:
    proposed = "mac.query_battery"
    # Stub percentage keeps demo deterministic on Linux
    return CapabilityResult(True, "battery~87% (stub)", proposed, executed=False)


def _screenshot(path: str | None, *, dry_run: bool) -> CapabilityResult:
    target = path or "~/Desktop/call-my-mac-screenshot.png"
    if any(c in target for c in [";", "|", "&", "`", "$", "\n"]):
        return CapabilityResult(False, "invalid path", "mac.screenshot", executed=False)
    proposed = f"mac.screenshot path={target}"
    return CapabilityResult(True, f"would save screenshot to {target}", proposed, executed=False)
