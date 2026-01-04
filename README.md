# Home Assistant Nostr Notifier

A Home Assistant custom integration that sends notifications as encrypted Nostr direct messages using NIP-17, NIP-59, and NIP-44.

## Features

- Multiple "topics" - each topic has its own Nostr keypair and recipient list
- NIP-17 encrypted DMs delivered to recipients' inbox relays (kind 10050)
- NIP-59 gift wraps with NIP-44 encryption
- Automatic kind 0 metadata publishing for topics (sets profile name)
- Fire-and-forget sending - non-blocking Home Assistant notify calls
- Configurable per topic via HA UI (no YAML required)
- Subject formatting with Markdown

## Installation

### Via HACS (Recommended)

1. In HACS, go to Settings > Custom Repositories
2. Add this repository URL (e.g., `https://github.com/psic4t/ha-nostr-notifier`)
3. Go to Explore > search for "Home Assistant Nostr Notifier"
4. Click "Download" and follow the prompts
5. Restart Home Assistant
6. Go to Settings > Devices & services > Add integration > "Home Assistant Nostr Notifier"

### Manual Installation

1. Copy `custom_components/ha_nostr_notifier/` to your Home Assistant `custom_components/` directory
2. Restart Home Assistant
3. Go to Settings > Devices & services > Add integration > "Home Assistant Nostr Notifier"

## Configuration

### Creating a Topic

1. Click "Add Integration" and select "Home Assistant Nostr Notifier"
2. Enter a topic name (e.g., "Kitchen Alerts")
3. Optionally add recipients as npub strings (one per line)
4. Click "Submit"

The integration will:
- Generate a new Nostr keypair for the topic
- Derive a stable slug (used in the entity_id)
- Publish kind 0 metadata to bootstrap relays

### Editing a Topic

1. Go to Settings > Devices & services > [Your Topic] > Configure
2. Change the topic name or recipient list
3. Click "Submit"

The integration will republish kind 0 metadata when the topic name or recipients change.

## Usage

### Sending Notifications

After creating a topic, a `notify.nostr_<topic_slug>` service becomes available.

Example automation:

```yaml
automation:
  - alias: "Kitchen Motion Notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.kitchen_motion
        to: "on"
    action:
      - service: notify.nostr_kitchen_alerts
        data:
          message: "Motion detected in the kitchen"
          title: "Kitchen Motion"
          data:
            subject: "Kitchen Alert" # Preferred over title
```

### Service Parameters

- `message` (required): The notification body
- `title` (optional): Subject/fallback title
- `data.subject` (optional): Subject that will be formatted as Markdown (`*<subject>*`)

If both `title` and `data.subject` are provided, `data.subject` takes precedence.

## Relay Configuration

The integration uses a fixed bootstrap relay list for discovery and metadata publishing:

- `wss://nostr.data.haus`
- `wss://relay.damus.io`
- `wss://nos.lol`
- `wss://relay.primal.net`
- `wss://purplepag.es`

DMs are sent only to relays discovered from each recipient's kind 10050 event.

### Recipient Requirements

Recipients must have published a kind 10050 event (inbox relays metadata). If a recipient lacks this event:
- The integration logs an info message
- No DM is sent to that recipient

## Security Notes

### Private Key Storage

- Topic private keys are stored in Home Assistant's config entry storage
- Treat your Home Assistant backup files as containing sensitive cryptographic material
- Do not share backup files publicly
- Consider encrypting backups

### Network Security

- Connections to Nostr relays use secure WebSockets (`wss://`)
- Messages are encrypted end-to-end using NIP-44
- Messages are additionally wrapped with NIP-59 gift wraps

## Troubleshooting

### "No kind 10050 event found for recipient"

The recipient has not published inbox relay metadata (kind 10050). Ask the recipient to:
1. Configure their messaging relays in their Nostr client
2. Ensure the client publishes kind 10050 to a well-connected relay

### "Timed out connecting to bootstrap relays"

Network connectivity or relay unavailability. The integration will retry on the next notification.

### Messages not arriving

1. Check recipient's inbox relays are online
2. Verify the recipient's kind 10050 event lists correct relays
3. Check Home Assistant logs for send errors

## Development

### Requirements

- Home Assistant 2024.x or later
- Python 3.11 or later
- `nostr-sdk==0.35.1` (automatically installed)

### Running Tests

```bash
python3 -m py_compile custom_components/ha_nostr_notifier/*.py
```

## License

[Your License Here]

## Contributing

Contributions welcome! Please open an issue or PR on GitHub.
