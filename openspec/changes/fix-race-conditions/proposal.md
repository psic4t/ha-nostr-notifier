## Why

The current notification sending implementation shares a single `NostrClient` instance across concurrent tasks when sending to multiple recipients. This creates race conditions where concurrent calls to `add_relay()`, `connect()`, and other mutating operations could corrupt state in the underlying `nostr_sdk` Rust library. Additionally, fire-and-forget tasks don't integrate with Home Assistant's lifecycle, and there's no cleanup of WebSocket connections.

## What Changes

- Isolate client instances per-recipient to eliminate shared mutable state during parallel sends
- Add proper client cleanup with `close()` method to prevent resource leaks
- Use Home Assistant's task API (`async_create_background_task`) for proper lifecycle management
- Add defensive timeout wrappers around SDK connection operations
- Improve error handling in config flow for invalid npub validation

## Capabilities

### New Capabilities

(none - this is a bug fix/safety improvement to existing functionality)

### Modified Capabilities

- `nostr-dm-delivery`: Add client isolation and cleanup requirements for safe concurrent sending

## Impact

- Affected code:
  - `custom_components/ha_nostr_notifier/__init__.py` - task management
  - `custom_components/ha_nostr_notifier/notify.py` - client isolation
  - `custom_components/ha_nostr_notifier/nostr_client.py` - cleanup method, timeouts
  - `custom_components/ha_nostr_notifier/config_flow.py` - npub validation
- No breaking changes to user-facing API
- No changes to notification behavior from user perspective
