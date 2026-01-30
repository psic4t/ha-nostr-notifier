## ADDED Requirements

### Requirement: Client Isolation for Concurrent Sends

When sending notifications to multiple recipients in parallel, each recipient MUST be processed with an isolated `NostrClient` instance to prevent race conditions from shared mutable state.

#### Scenario: Parallel sends to multiple recipients
- **WHEN** a notification is sent to 3 recipients simultaneously
- **THEN** each recipient's send operation uses its own `NostrClient` instance
- **AND** no shared state is mutated concurrently

#### Scenario: One recipient fails
- **WHEN** sending to recipient A fails with an exception
- **THEN** sending to recipients B and C continues unaffected
- **AND** the failure is logged with a warning

### Requirement: Client Resource Cleanup

The `NostrClient` MUST provide a `close()` method that disconnects from all relays. This method MUST be called after send operations complete, regardless of success or failure.

#### Scenario: Successful send cleanup
- **WHEN** a DM is sent successfully
- **THEN** `close()` is called to disconnect WebSocket connections

#### Scenario: Failed send cleanup
- **WHEN** a DM send fails with an exception
- **THEN** `close()` is still called in the finally block
- **AND** cleanup errors are logged at debug level

### Requirement: Home Assistant Task Integration

Background tasks (such as metadata publishing) MUST use Home Assistant's `async_create_background_task()` API instead of raw `asyncio.create_task()` for proper lifecycle management.

#### Scenario: Integration shutdown during metadata publish
- **WHEN** Home Assistant shuts down while metadata is being published
- **THEN** the background task is cancelled gracefully
- **AND** no orphaned tasks remain

### Requirement: Defensive Timeout Handling

All SDK operations that may block (such as `wait_for_connection`) MUST be wrapped with explicit `asyncio.wait_for()` timeouts as defense-in-depth.

#### Scenario: SDK timeout fails
- **WHEN** the SDK's internal timeout mechanism fails to trigger
- **THEN** the asyncio timeout wrapper triggers after the configured timeout
- **AND** a timeout warning is logged
