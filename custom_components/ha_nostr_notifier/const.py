"""Constants for the Home Assistant Nostr notifier integration."""
from __future__ import annotations

DOMAIN = "ha_nostr_notifier"

CONF_TOPIC_NAME = "topic_name"
CONF_RECIPIENTS = "recipients"
CONF_TOPIC_SLUG = "topic_slug"
CONF_PRIVATE_KEY = "private_key"

DEFAULT_BOOTSTRAP_RELAYS = [
    "wss://nostr.data.haus",
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.primal.net",
    "wss://purplepag.es",
]

DISCOVERY_TIMEOUT_SEC = 5
PUBLISH_TIMEOUT_SEC = 5

KIND_10050_RELAY_TAG = "relay"
