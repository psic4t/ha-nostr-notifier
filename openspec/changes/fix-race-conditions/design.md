## Context

The `ha-nostr-notifier` integration sends Nostr DMs to multiple recipients in parallel using `asyncio.gather()`. Currently, a single `NostrClient` instance is created per `async_send_message` call and shared across all parallel `_send_to_recipient` tasks. The underlying `nostr_sdk` is a Rust-backed library where concurrent mutations to the same `Client` object may cause undefined behavior.

Additionally:
- Fire-and-forget metadata publishing uses raw `asyncio.create_task()` without Home Assistant lifecycle integration
- `NostrClient` never calls disconnect, potentially leaking WebSocket connections
- Config flow lacks graceful handling of invalid npub formats

## Goals / Non-Goals

**Goals:**
- Eliminate race conditions when sending to multiple recipients concurrently
- Ensure proper resource cleanup (WebSocket connections)
- Integrate background tasks with Home Assistant's lifecycle
- Improve error messages for invalid user input

**Non-Goals:**
- Connection pooling or client reuse optimization (future enhancement)
- Changing the notification delivery semantics
- Adding retry logic or delivery guarantees

## Decisions

### 1. Per-Recipient Client Isolation

Create a new `NostrClient` instance for each recipient within `_send_to_recipient`, rather than sharing one client across parallel tasks.

**Rationale:** This is the simplest approach that completely eliminates shared mutable state. Each parallel task operates on its own isolated client, making concurrent operations safe.

**Alternatives considered:**
- **Serialized sending with asyncio.Lock**: Rejected because it eliminates parallelism benefits and adds complexity
- **Thread-safe client with internal locking**: Rejected because it requires understanding `nostr_sdk` internals and adds significant complexity for marginal benefit

### 2. Explicit Client Cleanup

Add `async def close()` method to `NostrClient` that calls `self._client.disconnect()`. Call it in a `finally` block after send operations.

**Rationale:** Ensures WebSocket connections are properly closed regardless of success/failure, preventing resource leaks over time.

**Alternatives considered:**
- **Context manager pattern**: Rejected as overkill for the current usage pattern; `finally` block is simpler
- **Relying on garbage collection**: Rejected because Python GC timing is unpredictable and connections may linger

### 3. Home Assistant Background Task API

Replace `asyncio.create_task()` with `hass.async_create_background_task()` for fire-and-forget operations.

**Rationale:** 
- Integrates with HA's lifecycle (tasks cancelled on shutdown)
- Better error tracking and logging
- Named tasks aid debugging

### 4. Defensive Timeout Wrapping

Wrap `wait_for_connection()` calls with explicit `asyncio.wait_for()` as defense-in-depth.

**Rationale:** The SDK has its own timeout, but wrapping with asyncio ensures Python-level control if the SDK timeout fails.

### 5. Graceful npub Validation

Wrap `decode_npub_to_hex()` calls in try/except and set specific form errors.

**Rationale:** Provides user-friendly feedback instead of a generic failure when invalid npub is entered.

## Risks / Trade-offs

- **More connections per notification**: Each recipient now creates its own client and connections, increasing resource usage. Mitigated by the fact that connections are short-lived and cleaned up promptly.

- **Relay cache not shared**: Per-recipient clients don't share the relay discovery cache. Mitigated by the fact that each send already created a new client, so this doesn't change current behavior.

- **SDK disconnect behavior unknown**: If `nostr_sdk.Client.disconnect()` throws or hangs, cleanup could fail. Mitigated by wrapping in try/except with debug logging.
