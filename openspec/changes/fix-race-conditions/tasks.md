## 1. NostrClient Cleanup Method

- [x] 1.1 Add `async def close()` method to `NostrClient` that calls `self._client.disconnect()`
- [x] 1.2 Wrap disconnect call in try/except with debug-level logging

## 2. Client Isolation in Notification Sending

- [x] 2.1 Modify `_send_to_recipient` to create its own `NostrClient` instance
- [x] 2.2 Remove `client` parameter from `_send_to_recipient` signature
- [x] 2.3 Update `async_send_message` to not create shared client
- [x] 2.4 Add `finally` block to `_send_to_recipient` that calls `client.close()`

## 3. Home Assistant Task Integration

- [x] 3.1 Replace `asyncio.create_task()` with `hass.async_create_background_task()` in `__init__.py`
- [x] 3.2 Add descriptive task name for debugging (e.g., `nostr_metadata_publish_{entry_id}`)

## 4. Defensive Timeout Handling

- [x] 4.1 Add `asyncio.wait_for()` wrapper around `wait_for_connection()` in `send_encrypted_dm`

## 5. Config Flow Validation

- [x] 5.1 Wrap `decode_npub_to_hex()` calls in try/except in `async_step_user`
- [x] 5.2 Wrap `decode_npub_to_hex()` calls in try/except in `async_step_init`
- [x] 5.3 Add `invalid_recipient` error key to form errors (using existing `invalid_npub` key)
- [x] 5.4 Add error string to `strings.json` and `translations/en.json` (already exists as `invalid_npub`)

## 6. Verification

- [ ] 6.1 Test sending notification to multiple recipients (manual)
- [ ] 6.2 Verify no unhandled exceptions in Home Assistant logs (manual)
- [ ] 6.3 Verify proper cleanup by checking for connection warnings (manual)
