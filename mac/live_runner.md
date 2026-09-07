# Live macOS runner (optional, on a real Mac)

Phase 0 capabilities return `proposed_cmd` strings such as `mac.activate_app name=Safari`.

On Darwin, to actually run allowlisted actions:

1. Keep `CALL_MY_MAC_DRY_RUN=0` only when you intentionally want live effects.
2. Set `CALL_MY_MAC_ALLOW_LIVE=1`.
3. Implement `live_runner.py` (not required for text demo) that maps:
   - `open_app` → AppleScript activate for **allowlisted** app names only
   - `say` → `/usr/bin/say`
   - `get_battery` → `pmset -g batt`
   - `screenshot` → `screencapture` after `/v1/confirm`

Never pipe model text into a shell. Always resolve through the allowlist in `agent/capabilities.py`.
