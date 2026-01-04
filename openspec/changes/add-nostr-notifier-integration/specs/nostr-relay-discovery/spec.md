## ADDED Requirements

### Requirement: Bootstrap Relay List
The system SHALL use a fixed global bootstrap relay list for Nostr relay discovery operations.

#### Scenario: Relay discovery starts
- **WHEN** the integration needs to discover recipient messaging relays
- **THEN** it SHALL query the configured bootstrap relay list

### Requirement: Default Bootstrap Relays
The default bootstrap relay list SHALL be:
- `wss://nostr.data.haus`
- `wss://relay.damus.io`
- `wss://nos.lol`
- `wss://relay.primal.net`
- `wss://purplepag.es`

#### Scenario: No user configuration
- **WHEN** the user does not override relay settings (if supported)
- **THEN** the integration SHALL use the default bootstrap relay list

### Requirement: Recipient Messaging Relay Discovery (kind 10050)
The system SHALL discover a recipient’s messaging relays by reading the recipient’s kind `10050` event and extracting `relay` tags.

#### Scenario: Recipient has kind 10050
- **GIVEN** the recipient has published a kind `10050` event with one or more `relay` tags
- **WHEN** the integration performs discovery
- **THEN** it SHALL return those relays as the recipient’s messaging relays

### Requirement: Parallel Discovery
The system SHALL query bootstrap relays in parallel for kind `10050` discovery.

#### Scenario: Some relays are slow
- **GIVEN** at least one bootstrap relay is slow or unreachable
- **WHEN** discovery runs
- **THEN** other bootstrap relays SHALL still be queried without waiting for the slow relay

### Requirement: Discovery Timeout
The system SHALL timebox relay discovery queries to 5 seconds.

#### Scenario: Relay does not respond
- **WHEN** a relay query does not complete within 5 seconds
- **THEN** the integration SHALL treat that relay query as failed

### Requirement: Discovery Cache
The system SHALL cache recipient messaging relays for a finite TTL to reduce repeated discovery queries.

#### Scenario: Recipient previously discovered
- **GIVEN** a recipient’s messaging relays were discovered recently
- **WHEN** another notification is sent to that recipient
- **THEN** the integration SHALL reuse cached relays until the TTL expires

### Requirement: Missing kind 10050 Handling
If no kind `10050` event can be found for a recipient, the system SHALL log an `info` message and SHALL skip DM sending to that recipient.

#### Scenario: Recipient has no kind 10050
- **GIVEN** no kind `10050` event is found via the bootstrap relays
- **WHEN** a notification is attempted
- **THEN** the integration SHALL log at `info` and skip sending to that recipient
