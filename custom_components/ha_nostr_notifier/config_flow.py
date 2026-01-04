"""Config flow for the Home Assistant Nostr notifier integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_PRIVATE_KEY,
    CONF_RECIPIENTS,
    CONF_TOPIC_NAME,
    CONF_TOPIC_SLUG,
    DOMAIN,
)
from .nostr_client import decode_npub_to_hex, generate_nostr_keypair
from .util import generate_topic_slug, parse_recipients

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TOPIC_NAME): str,
        vol.Optional(CONF_RECIPIENTS, default=""): str,
    }
)


def get_existing_slugs(hass: HomeAssistant) -> list[str]:
    """Get all existing topic slugs."""
    slugs = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        if slug := entry.data.get(CONF_TOPIC_SLUG):
            slugs.append(slug)
    return slugs


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nostr notifier."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate topic name
            topic_name = user_input[CONF_TOPIC_NAME].strip()
            if not topic_name:
                errors[CONF_TOPIC_NAME] = "invalid_topic_name"
            else:
                # Validate recipients if provided
                recipients_text = user_input[CONF_RECIPIENTS]
                if recipients_text:
                    recipients = parse_recipients(recipients_text)
                    recipients_hex = [
                        decode_npub_to_hex(npub) for npub in recipients
                    ]
                else:
                    recipients_hex = []

                if not errors:
                    # Generate stable slug
                    existing_slugs = get_existing_slugs(self.hass)
                    slug = generate_topic_slug(topic_name, existing_slugs)

                    # Generate Nostr keypair
                    private_key_hex, public_key_hex = await generate_nostr_keypair()

                    # Create config entry
                    data = {
                        CONF_TOPIC_NAME: topic_name,
                        CONF_TOPIC_SLUG: slug,
                        CONF_PRIVATE_KEY: private_key_hex,
                        CONF_RECIPIENTS: recipients_hex,
                    }

                    return self.async_create_entry(
                        title=topic_name,
                        data=data,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return HaNostrNotifierOptionsFlow(config_entry)


class HaNostrNotifierOptionsFlow(config_entries.OptionsFlow):
    """Handle the options flow for editing topic."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        # In recent Home Assistant versions `OptionsFlow.config_entry` is a read-only
        # property backed by `_config_entry`.
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the options form."""
        errors = {}

        if user_input is not None:
            # Validate topic name
            topic_name = user_input[CONF_TOPIC_NAME].strip()
            if not topic_name:
                errors[CONF_TOPIC_NAME] = "invalid_topic_name"
            else:
                # Validate recipients if provided
                recipients_text = user_input[CONF_RECIPIENTS]
                if recipients_text:
                    recipients = parse_recipients(recipients_text)
                    recipients_hex = [
                        decode_npub_to_hex(npub) for npub in recipients
                    ]
                else:
                    recipients_hex = []

                if not errors:
                    # Update options - preserve original slug and private key
                    data = dict(self.config_entry.data)
                    data[CONF_TOPIC_NAME] = topic_name
                    data[CONF_RECIPIENTS] = recipients_hex

                    self.hass.config_entries.async_update_entry(
                        self.config_entry, data=data
                    )

                    return self.async_create_entry(title="", data=None)

        # Pre-fill with current values
        current_topic_name = self.config_entry.data.get(CONF_TOPIC_NAME, "")
        current_recipients_hex = self.config_entry.data.get(CONF_RECIPIENTS, [])

        # The config entry stores recipients as hex pubkeys, but the UI expects
        # `npub...` values.
        current_recipients: list[str] = []
        try:
            from nostr_sdk import PublicKey

            for public_key_hex in current_recipients_hex:
                try:
                    current_recipients.append(PublicKey.parse(public_key_hex).to_bech32())
                except Exception:
                    current_recipients.append(public_key_hex)
        except Exception:
            current_recipients = list(current_recipients_hex)

        current_recipients_text = "\n".join(current_recipients)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TOPIC_NAME, default=current_topic_name): str,
                    vol.Optional(
                        CONF_RECIPIENTS, default=current_recipients_text
                    ): str,
                }
            ),
            errors=errors,
        )
