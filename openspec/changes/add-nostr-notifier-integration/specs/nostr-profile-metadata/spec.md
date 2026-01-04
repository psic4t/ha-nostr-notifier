## ADDED Requirements

### Requirement: Publish Topic Profile Metadata (kind 0)
The system SHALL publish a kind `0` metadata event for each topic so recipients can display a meaningful sender name.

#### Scenario: Topic created
- **WHEN** a topic is created
- **THEN** the integration SHALL publish a kind `0` event for that topic

#### Scenario: Topic renamed
- **WHEN** a topic name is edited
- **THEN** the integration SHALL publish an updated kind `0` event for that topic

### Requirement: Metadata Fields
The kind `0` event content SHALL set both `name` and `display_name` to the configured topic name.

#### Scenario: Topic name is set
- **WHEN** the topic name is `Kitchen Alerts`
- **THEN** the kind `0` content SHALL set `name` and `display_name` to `Kitchen Alerts`

### Requirement: Metadata Publishing Targets
The system SHALL publish kind `0` metadata events to both:
1) the bootstrap relay list, and
2) the union of all configured recipients’ messaging relays (kind `10050`).

#### Scenario: Topic has recipients
- **GIVEN** a topic has one or more recipients with discoverable messaging relays
- **WHEN** the integration publishes kind `0` metadata
- **THEN** it SHALL publish to the bootstrap relays and the recipients’ messaging relays

### Requirement: Fire-and-Forget Metadata Publishing
Publishing kind `0` metadata SHALL be best-effort and SHALL NOT block Home Assistant UI actions.

#### Scenario: Relay publish fails
- **WHEN** a metadata publish to a relay fails
- **THEN** the integration SHALL log the failure and continue without raising a user-facing error
