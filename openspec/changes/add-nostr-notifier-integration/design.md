## Context
This change introduces a new Home Assistant notification integration that sends encrypted Nostr DMs. It is a new subsystem (custom component + async I/O + cryptographic event construction) and introduces a third-party dependency for cryptographic correctness.

## Goals / Non-Goals
- Goals:
  - Provide a HACS-installable `notify.*` endpoint in Home Assistant.
  - Support multiple independently-configured topics, each with its own generated Nostr keypair.
  - Deliver messages using NIP-17 semantics (gift wrap based) with NIP-59 + NIP-44.
  - Discover recipient inbox relays via kind `10050` and publish to those relays.
  - Publish kind `0` metadata for topics so recipients see a readable sender name.
  - Keep the notify call non-blocking (fire-and-forget).

- Non-Goals:
  - Full NIP-17 sender self-copy behavior.
  - Recipient identifiers beyond `npub` (e.g. NIP-05, `nprofile`) in v1.
  - Receiving / decrypting messages inside Home Assistant.
  - Advanced retry queues or delivery guarantees.

## High-level Architecture
- Home Assistant config entries represent topics.
- Each topic registers a notify entity/service with a stable slug (derived from initial topic name).
- A small internal Nostr client module handles:
  - NIP-19 decoding (`npub`)
  - kind `10050` lookup against bootstrap relays
  - NIP-59 event construction (rumor -> seal -> gift wrap)
  - NIP-44 encryption and event signing
  - parallel publish to a set of relays with timeouts

## Decisions
- Dependency: use `nostr-sdk` for cryptographic primitives and event construction.
  - Rationale: correct NIP-44 + NIP-59 implementation is security-sensitive and easy to get wrong.
  - Trade-off: introduces Rust-backed wheels that must be available for HA environments.

- Relay strategy:
  - A fixed, global bootstrap relay list is used for relay discovery and as a baseline publishing target for metadata.
  - Recipient DM delivery publishes to the recipient’s inbox relays from kind `10050`.
  - Profile metadata (kind `0`) publishes to both: (a) bootstrap relays and (b) union of recipients’ inbox relays.

- Fire-and-forget sending:
  - Home Assistant notify calls schedule async tasks and return quickly.
  - Errors are logged; delivery is best-effort.

- Topic naming:
  - `topic_name` is user-editable and controls the published Nostr profile name.
  - `topic_slug` is derived on initial creation and remains stable for the notify entity id.

- Subject handling:
  - Do not rely on client support for custom tags.
  - Prefer `data.subject` over `title` and format as Markdown in the message body.

## Risks / Trade-offs
- Wheel availability: mitigate by pinning `nostr-sdk` to a version with broad wheel coverage and documenting supported platforms.
- Key storage: private keys will live in HA storage; mitigate by:
  - clear documentation warnings
  - avoiding logging secrets
  - minimizing exposure via services/events
- Relay connectivity: some relays may be down/slow; mitigate via parallel querying and strict timeouts.

## Migration Plan
- New integration; no migration needed.

## Open Questions
- None for this proposal; behavior decisions are specified in proposal/spec deltas.
