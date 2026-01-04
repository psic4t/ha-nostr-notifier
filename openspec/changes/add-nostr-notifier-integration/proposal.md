# Change: Add Home Assistant Nostr notifier integration

## Why
Home Assistant has a generic notification service interface, but Nostr-native notification delivery (encrypted DMs to Nostr recipients) is not available out of the box. This change adds a HACS-installable integration that can be used as a `notify.*` endpoint while delivering notifications as NIP-17 encrypted DMs.

## What Changes
- Add a new HACS custom integration named `ha-nostr-notifier` that registers one or more `notify.*` services.
- Introduce the concept of **topics** (multiple independent Nostr identities), each with its own generated keypair.
- Deliver notifications as NIP-17 DMs using NIP-59 (seals/gift wraps) and NIP-44 encryption to the recipient’s messaging relays (kind `10050`).
- Publish the topic’s Nostr profile name via kind `0` metadata events so recipients see a meaningful sender identity.
- Use a fixed, global bootstrap relay list for discovery and metadata publishing.
- Sending is best-effort (fire-and-forget): Home Assistant service calls should not block on relay delivery.

## Constraints / Decisions
- Distribution is via HACS (custom component), not HA Core.
- Topics always generate new keys (no `nsec` import).
- Default-send to all recipients configured for a topic.
- Skip NIP-17 sender self-copy.
- If a recipient has no kind `10050` event, log at `info` and skip sending to that recipient.
- Timeouts: 5s for relay queries, 5s for publishes.
- Relay discovery queries run in parallel.
- Subject handling: prefer `data.subject` over `title` and format as Markdown (`*subject*`) instead of Nostr tags.
- Topic notify service id uses a stable slug derived from the initial topic name (collisions auto-suffixed).

## Impact
- Affected specs (new capabilities):
  - `nostr-notification-endpoint`
  - `nostr-relay-discovery`
  - `nostr-profile-metadata`
  - `nostr-dm-delivery`
- Affected code (new):
  - `custom_components/ha_nostr_notifier/*`
  - `hacs.json`, `README.md`
- External dependencies:
  - Adds `nostr-sdk` Python package (Rust-backed wheels) for NIP-44/NIP-59 primitives.

## Risks
- Dependency wheel availability varies by platform/architecture; HACS installs may fail if wheels are missing.
- Private key storage within Home Assistant’s config entry storage needs explicit security guidance (backup handling).
