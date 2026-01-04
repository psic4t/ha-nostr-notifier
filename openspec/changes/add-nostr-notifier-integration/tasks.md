## 1. Implementation
- [x] 1.1 Create HACS skeleton (`hacs.json`, integration folder)
- [x] 1.2 Add `manifest.json` with pinned `nostr-sdk` requirement
- [x] 1.3 Implement config flow: create topic, generate keys, stable slug
- [x] 1.4 Implement options flow: rename topic, edit recipients
- [x] 1.5 Implement recipient kind `10050` discovery (parallel) + TTL cache
- [x] 1.6 Implement kind `0` metadata publishing to bootstrap + recipient relays
- [x] 1.7 Implement NIP-17 DM sending (NIP-59 + NIP-44) fire-and-forget
- [x] 1.8 Register notify entities/services per topic (stable entity_id)
- [x] 1.9 Subject formatting: `data.subject` > `title`, emit `*subject*` markdown

## 2. Validation
- [x] 2.1 Run Python syntax check on all files
- [x] 2.2 Skip HA linting (requires HA environment)

## 3. Documentation
- [x] 3.1 Write `README.md` setup instructions (HACS)
- [x] 3.2 Document default relay list and kind `10050` requirement
- [x] 3.3 Document key storage and backup security implications
