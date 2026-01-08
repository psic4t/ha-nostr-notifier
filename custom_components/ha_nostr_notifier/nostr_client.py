"""Nostr client for key generation, event construction, and relay I/O."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_BOOTSTRAP_RELAYS,
    DISCOVERY_TIMEOUT_SEC,
    PUBLISH_TIMEOUT_SEC,
    KIND_10050_RELAY_TAG,
)

_LOGGER = logging.getLogger(__name__)

KIND_METADATA = 0
KIND_INBOX_RELAYS = 10050


class NostrClient:
    """Client for Nostr operations."""

    def __init__(self, private_key_hex: str) -> None:
        """Initialize Nostr client with a private key."""
        from nostr_sdk import Keys, NostrSigner, Client, RelayUrl

        self._keys = Keys.parse(private_key_hex)
        self._signer = NostrSigner.keys(self._keys)
        self._client = Client(self._signer)
        self._relay_cache: dict[str, tuple[list[str], float]] = {}
        self._cache_ttl = 3600.0

    async def _ensure_connected(self) -> None:
        """Ensure client is connected to bootstrap relays."""
        from nostr_sdk import RelayUrl

        for relay_url_str in DEFAULT_BOOTSTRAP_RELAYS:
            try:
                relay_url = RelayUrl.parse(relay_url_str)
                await self._client.add_relay(relay_url)
            except Exception as e:
                _LOGGER.warning("Failed to add relay %s: %s", relay_url_str, e)

        try:
            await self._client.connect()
            # Wait for connections to be established
            await self._client.wait_for_connection(timedelta(seconds=DISCOVERY_TIMEOUT_SEC))
        except Exception as e:
            _LOGGER.warning("Failed to connect to bootstrap relays: %s", e)

    async def _create_discovery_client(self) -> Any:
        """Create a temporary client for discovery (no signer needed)."""
        from nostr_sdk import Client, RelayUrl

        client = Client()

        for relay_url_str in DEFAULT_BOOTSTRAP_RELAYS:
            try:
                relay_url = RelayUrl.parse(relay_url_str)
                await client.add_relay(relay_url)
            except Exception as e:
                _LOGGER.debug("Failed to add discovery relay %s: %s", relay_url_str, e)

        try:
            await client.connect()
            # Wait for connections to be established before returning
            await client.wait_for_connection(timedelta(seconds=DISCOVERY_TIMEOUT_SEC))
        except Exception as e:
            _LOGGER.warning("Failed to connect discovery client: %s", e)
            return None

        return client

    async def discover_recipient_relays(self, recipient_pubkey_hex: str) -> list[str]:
        """Discover recipient's messaging relays from kind 10050 with TTL cache."""
        from nostr_sdk import Filter, Kind, PublicKey

        if recipient_pubkey_hex in self._relay_cache:
            relays, expiry = self._relay_cache[recipient_pubkey_hex]
            if time.time() < expiry:
                _LOGGER.debug(
                    "Using cached relays for recipient %s",
                    recipient_pubkey_hex,
                )
                return relays

        client = await self._create_discovery_client()
        if client is None:
            _LOGGER.warning("Could not create discovery client")
            return []

        try:
            pubkey = PublicKey.parse(recipient_pubkey_hex)
            filter_obj = Filter().kind(Kind(KIND_INBOX_RELAYS)).author(
                pubkey
            ).limit(1)

            events = await asyncio.wait_for(
                client.fetch_events(filter_obj, timedelta(seconds=DISCOVERY_TIMEOUT_SEC)),
                timeout=DISCOVERY_TIMEOUT_SEC,
            )
        except asyncio.TimeoutError:
            _LOGGER.warning("Timed out querying kind 10050 for recipient %s", recipient_pubkey_hex)
            return []
        except Exception as e:
            _LOGGER.warning("Failed to query kind 10050: %s", e)
            return []

        # Events object is not directly iterable in nostr-sdk 0.44.x
        # Use .is_empty() and .first() or .to_vec() to access events
        if events.is_empty():
            _LOGGER.info("No kind 10050 event found for recipient %s", recipient_pubkey_hex)
            return []

        event = events.first()
        if event is None:
            _LOGGER.info("No kind 10050 event found for recipient %s", recipient_pubkey_hex)
            return []

        relays = []

        try:
            event_json = json.loads(event.as_json())
            for tag in event_json.get("tags", []):
                if isinstance(tag, list) and len(tag) > 0:
                    if tag[0] == KIND_10050_RELAY_TAG and len(tag) > 1:
                        relay = tag[1]
                        if relay.startswith(("wss://", "ws://")):
                            relays.append(relay)
        except Exception as e:
            _LOGGER.warning("Failed to parse kind 10050 tags: %s", e)

        if relays:
            _LOGGER.debug(
                "Found %d messaging relay(s) for recipient %s: %s",
                len(relays),
                recipient_pubkey_hex,
                relays,
            )
            expiry = time.time() + self._cache_ttl
            self._relay_cache[recipient_pubkey_hex] = (relays, expiry)
        else:
            _LOGGER.info(
                "Kind 10050 event found for recipient %s but no relay tags present",
                recipient_pubkey_hex,
            )

        return relays

    async def publish_metadata_event(
        self,
        topic_name: str,
        target_relays: list[str],
        timeout_sec: float = PUBLISH_TIMEOUT_SEC,
    ) -> None:
        """Publish kind 0 metadata event for topic."""
        from nostr_sdk import Metadata, RelayUrl

        try:
            metadata = Metadata().name(topic_name).display_name(topic_name).picture(
                "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/New_Home_Assistant_logo.svg/250px-New_Home_Assistant_logo.svg.png"
            )
            await self._ensure_connected()

            for relay_url_str in target_relays:
                try:
                    relay_url = RelayUrl.parse(relay_url_str)
                    await self._client.add_relay(relay_url)
                except Exception as e:
                    _LOGGER.warning("Failed to add metadata relay %s: %s", relay_url_str, e)

            try:
                await self._client.set_metadata(metadata)
                _LOGGER.info(
                    "Published metadata for topic %s to %d relay(s)",
                    topic_name,
                    len(target_relays),
                )
            except Exception as e:
                _LOGGER.warning("Failed to publish metadata event: %s", e)
        except Exception as e:
            _LOGGER.warning("Error preparing metadata: %s", e)

    async def send_encrypted_dm(
        self,
        recipient_pubkey_hex: str,
        message: str,
        recipient_relays: list[str],
        timeout_sec: float = PUBLISH_TIMEOUT_SEC,
    ) -> None:
        """Send NIP-17 encrypted direct message."""
        from nostr_sdk import PublicKey, RelayUrl

        if not recipient_relays:
            _LOGGER.info(
                "No messaging relays for recipient %s, skipping DM send",
                recipient_pubkey_hex,
            )
            return

        try:
            recipient_pubkey = PublicKey.parse(recipient_pubkey_hex)

            relay_urls = []
            for relay_url_str in recipient_relays:
                try:
                    relay_url = RelayUrl.parse(relay_url_str)
                    relay_urls.append(relay_url)
                except Exception as e:
                    _LOGGER.warning("Failed to parse relay URL %s: %s", relay_url_str, e)

            if not relay_urls:
                _LOGGER.warning("No valid relay URLs to send to")
                return

            # Add recipient's relays to the client and connect
            for relay_url in relay_urls:
                try:
                    await self._client.add_relay(relay_url)
                except Exception as e:
                    _LOGGER.debug("Failed to add relay %s: %s", relay_url, e)

            await self._client.connect()
            await self._client.wait_for_connection(timedelta(seconds=timeout_sec))

            try:
                await asyncio.wait_for(
                    self._client.send_private_msg_to(
                        relay_urls, recipient_pubkey, message, []
                    ),
                    timeout=timeout_sec,
                )
                _LOGGER.debug(
                    "Sent encrypted DM to recipient %s via %d relay(s)",
                    recipient_pubkey_hex,
                    len(relay_urls),
                )
            except asyncio.TimeoutError:
                _LOGGER.warning("Timed out sending DM to recipient %s", recipient_pubkey_hex)
            except Exception as e:
                _LOGGER.warning("Failed to send DM to recipient %s: %s", recipient_pubkey_hex, e)
        except Exception as e:
            _LOGGER.warning("Error preparing encrypted DM: %s", e)


async def generate_nostr_keypair() -> tuple[str, str]:
    """Generate a new Nostr keypair.

    Returns (private_key_hex, public_key_hex).
    """
    from nostr_sdk import Keys

    keys = Keys.generate()
    return keys.secret_key().to_hex(), keys.public_key().to_hex()


def decode_npub_to_hex(npub: str) -> str:
    """Decode a npub string to a hex public key."""
    from nostr_sdk import PublicKey

    pubkey = PublicKey.parse(npub)
    return pubkey.to_hex()
