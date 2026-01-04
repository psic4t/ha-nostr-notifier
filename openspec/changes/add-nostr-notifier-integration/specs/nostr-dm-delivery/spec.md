## ADDED Requirements

### Requirement: NIP-17 Encrypted Direct Message Delivery
The system SHALL deliver notifications as encrypted Nostr direct messages following NIP-17 message delivery semantics using NIP-59 and NIP-44.

#### Scenario: Notification delivered
- **WHEN** a user sends a notification via the topic notify service
- **THEN** the integration SHALL construct and publish the required NIP-59 events (rumor, seal, gift wrap) with NIP-44 encryption for each recipient

### Requirement: Recipient Relay Targeting
The system SHALL publish DM gift wrap events only to the recipient’s messaging relays as discovered from kind `10050`.

#### Scenario: Recipient inbox relays discovered
- **GIVEN** recipient messaging relays were discovered from kind `10050`
- **WHEN** a notification is sent
- **THEN** the integration SHALL publish gift wraps to those relays

### Requirement: No Sender Self-Copy
The system SHALL NOT publish a sender self-copy of NIP-17 DMs.

#### Scenario: DM sent
- **WHEN** a DM is sent to a recipient
- **THEN** the integration SHALL NOT additionally publish a self-copy for the sender

### Requirement: Fire-and-Forget Delivery
The system SHALL perform DM sending as best-effort and SHALL return control to the Home Assistant notify call without waiting for relay acknowledgements.

#### Scenario: Slow relay
- **GIVEN** relay publish operations are slow
- **WHEN** the notify service is called
- **THEN** the service call SHALL return without blocking on delivery

### Requirement: Publish Timeout
The system SHALL timebox publish attempts to 5 seconds per relay.

#### Scenario: Relay does not respond
- **WHEN** a publish attempt does not complete within 5 seconds
- **THEN** the integration SHALL treat that publish as failed and continue

### Requirement: Topic Key Generation Only
The system SHALL generate new Nostr keypairs for topics and SHALL NOT support importing private keys in v1.

#### Scenario: Topic created
- **WHEN** the user creates a topic
- **THEN** the integration SHALL generate a new keypair for the topic
