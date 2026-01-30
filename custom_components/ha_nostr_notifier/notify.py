"""Notify platform for Nostr notifier."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.notify import (
    BaseNotificationService,
    NotifyEntity,
    NotifyEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_PRIVATE_KEY,
    CONF_RECIPIENTS,
    CONF_TOPIC_NAME,
    CONF_TOPIC_SLUG,
    DOMAIN,
)
from .nostr_client import NostrClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nostr notifier notify platform."""
    topic_slug = entry.data.get(CONF_TOPIC_SLUG, "nostr")
    topic_name = entry.options.get(
        CONF_TOPIC_NAME,
        entry.data.get(CONF_TOPIC_NAME, "Nostr Topic"),
    )
    private_key = entry.data.get(CONF_PRIVATE_KEY, "")
    recipients = entry.options.get(
        CONF_RECIPIENTS,
        entry.data.get(CONF_RECIPIENTS, []),
    )

    _LOGGER.debug(
        "Setting up notify entity for topic %s (slug: %s) with %d recipients",
        topic_name,
        topic_slug,
        len(recipients),
    )

    entity = NostrNotifyEntity(
        entry,
        topic_slug,
        topic_name,
        private_key,
        recipients,
    )

    async_add_entities([entity])


class NostrNotifyEntity(NotifyEntity):
    """Entity for Nostr notifications."""

    _attr_supported_features = NotifyEntityFeature.TITLE

    def __init__(
        self,
        config_entry: ConfigEntry,
        topic_slug: str,
        topic_name: str,
        private_key: str,
        recipients: list[str],
    ) -> None:
        """Initialize the entity."""
        self._config_entry = config_entry
        self._topic_slug = topic_slug
        self._topic_name = topic_name
        self._private_key = private_key
        self._recipients = recipients

    @property
    def unique_id(self) -> str:
        """Return unique ID for this entity."""
        return f"{self._config_entry.entry_id}_{self._topic_slug}"

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._topic_name

    @property
    def should_poll(self) -> bool:
        """Return False because this entity pushes state."""
        return False

    async def async_send_message(self, message: str, **kwargs: Any) -> None:
        """Send a notification message."""
        client = NostrClient(self._private_key)
        try:
            subject = kwargs.get("data", {}).get("subject")
            if not subject:
                subject = kwargs.get("title")

            formatted_message = message
            if subject:
                formatted_message = f"**{subject}**\n\n{message}"

            _LOGGER.debug(
                "Sending Nostr notification to %d recipients",
                len(self._recipients),
            )

            tasks = []
            for recipient_hex in self._recipients:
                task = asyncio.create_task(
                    self._send_to_recipient(client, recipient_hex, formatted_message)
                )
                tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            await client.close()

    async def _send_to_recipient(
        self, client: NostrClient, recipient_hex: str, message: str
    ) -> None:
        """Send to a single recipient."""
        try:
            relays = await client.discover_recipient_relays(recipient_hex)
            if relays:
                await client.send_encrypted_dm(recipient_hex, message, relays)
        except Exception as e:
            _LOGGER.warning(
                "Failed to send to recipient %s: %s",
                recipient_hex,
                e,
            )
