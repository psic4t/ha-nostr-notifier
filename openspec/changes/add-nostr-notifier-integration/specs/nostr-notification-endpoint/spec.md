## ADDED Requirements

### Requirement: HACS-Installable Notification Integration
The system SHALL provide a HACS-installable Home Assistant custom integration named `ha-nostr-notifier` that can be used as a notification endpoint.

#### Scenario: User installs and configures
- **WHEN** the user installs the integration via HACS and adds it in Home Assistant
- **THEN** Home Assistant SHALL offer one or more `notify.*` entities/services provided by the integration

### Requirement: Topics As Independent Sender Identities
The system SHALL allow configuring multiple topics, where each topic has its own generated Nostr keypair and independent recipient list.

#### Scenario: Multiple topics exist
- **WHEN** the user creates two topics
- **THEN** the integration SHALL use distinct keypairs when sending notifications from each topic

### Requirement: Stable Notify Service Identifier
The system SHALL derive a stable notify identifier (slug) from the initial topic name and SHALL NOT change that identifier when the topic name is later edited.

#### Scenario: Topic is renamed
- **GIVEN** a topic was created with initial name `Kitchen`
- **WHEN** the user renames the topic to `Kitchen Alerts`
- **THEN** the notify entity/service identifier SHALL remain the same as created initially

### Requirement: Slug Collision Handling
The system SHALL ensure topic slugs are unique by auto-suffixing collisions (e.g., `_2`, `_3`).

#### Scenario: Duplicate topic names
- **WHEN** the user creates two topics with the same initial name
- **THEN** the integration SHALL assign distinct slugs to each topic

### Requirement: Default Send-To-All Recipients
The notify service for a topic SHALL send notifications to all recipients configured for that topic.

#### Scenario: Notification sent
- **GIVEN** a topic has multiple recipients configured
- **WHEN** the user calls the topic’s notify service
- **THEN** the integration SHALL attempt delivery to each configured recipient

### Requirement: Subject Formatting
The integration SHALL format a subject into the outgoing message body using Markdown and SHALL prefer `data.subject` over `title` when both are provided.

#### Scenario: Subject provided
- **WHEN** the notify call includes `data.subject` and `message`
- **THEN** the outgoing DM content SHALL be `*<subject>*` followed by a blank line and then the message body

#### Scenario: Both title and data.subject provided
- **WHEN** the notify call includes both `title` and `data.subject`
- **THEN** the integration SHALL use `data.subject` as the subject
