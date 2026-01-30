"""Home Assistant Nostr notifier integration."""
from __future__ import annotations

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_BOOTSTRAP_RELAYS,
    DISCOVERY_TIMEOUT_SEC,
    DOMAIN,
)
from .nostr_client import NostrClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: Final = [Platform.NOTIFY]

RELAY_CACHE_TTL_SEC = 3600


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Nostr notifier from a config entry."""
    _LOGGER.info("Setting up Nostr notifier integration for entry: %s", entry.title)

    hass.data.setdefault(DOMAIN, {})
    private_key = entry.data.get("private_key")
    client = NostrClient(private_key)
    hass.data[DOMAIN][entry.entry_id] = {"entry": entry, "client": client}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Publish metadata after entry setup (fire-and-forget with HA lifecycle integration)
    hass.async_create_background_task(
        _publish_topic_metadata(hass, entry, client),
        name=f"nostr_metadata_publish_{entry.entry_id}",
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Nostr notifier integration for entry: %s", entry.title)

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _publish_topic_metadata(
    hass: HomeAssistant,
    entry: ConfigEntry,
    client: NostrClient,
) -> None:
    """Publish topic metadata (kind 0) to bootstrap and recipient relays."""
    topic_name = entry.options.get("topic_name", entry.data.get("topic_name", "Unknown"))

    relays = list(DEFAULT_BOOTSTRAP_RELAYS)
    recipients_hex = entry.options.get("recipients", entry.data.get("recipients", []))

    for recipient_hex in recipients_hex:
        recipient_relays = await client.discover_recipient_relays(recipient_hex)
        for relay in recipient_relays:
            if relay not in relays:
                relays.append(relay)

    if relays:
        await client.publish_metadata_event(topic_name, relays)
        _LOGGER.info("Published metadata for topic %s to %d relays", topic_name, len(relays))
    else:
        _LOGGER.warning("No relays available for metadata publish")
