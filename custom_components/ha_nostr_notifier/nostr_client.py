"""Nostr client for key generation, event construction, and relay I/O."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import nostr_sdk as sdk
from nostr_sdk import Keys, RelayPool, Client, Filter, UnsignedEvent, Tag
from nostr_sdk.nip59 import GiftSeal, GiftWrap

from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_BOOTSTRAP_RELAYS,
    DISCOVERY_TIMEOUT_SEC,
    PUBLISH_TIMEOUT_SEC,
    KIND_10050_RELAY_TAG,
)

_LOGGER = logging.getLogger(__name__)

KIND_TEXT_NOTE = 1
KIND_ENCRYPTED_DIRECT_MESSAGE = 4
KIND_METADATA = 0
KIND_RUMOR = 14
KIND_SEAL = 13
KIND_GIFT_WRAP = 1059
KIND_INBOX_RELAYS = 10050


class NostrClient:
    """Client for Nostr operations."""

    def __init__(self, private_key_hex: str) -> None:
        """Initialize Nostr client with a private key."""
        self._keys = Keys.parse(private_key_hex)
        self._pool = RelayPool()
        self._client = Client(self._pool)
        self._relay_cache: dict[str, tuple[list[str], float]] = {}
        self._cache_ttl = 3600.0

    async def _connect_and_query(
        self, filter_obj: Filter, timeout_sec: float = DISCOVERY_TIMEOUT_SEC
    ) -> list[Any]:
        """Connect to bootstrap relays and query events."""
        self._pool.clear()

        for relay_url in DEFAULT_BOOTSTRAP_RELAYS:
            self._pool.add_relay(relay_url)

        try:
            await asyncio.wait_for(self._pool.connect(), timeout=timeout_sec)
        except asyncio.TimeoutError:
            _LOGGER.warning("Timed out connecting to bootstrap relays")
            return []
        except Exception as e:
            _LOGGER.warning("Failed to connect to bootstrap relays: %s", e)
            return []

        try:
            events = await self._client.get_events_of([filter_obj], timeout_sec)
            return events
        except asyncio.TimeoutError:
            _LOGGER.warning("Timed out querying events from bootstrap relays")
            return []
        except Exception as e:
            _LOGGER.warning("Failed to query events: %s", e)
            return []

    async def discover_recipient_relays(self, recipient_pubkey_hex: str) -> list[str]:
        """Discover recipient's messaging relays from kind 10050 with TTL cache."""
        # Check cache first
        import time
        if recipient_pubkey_hex in self._relay_cache:
            relays, expiry = self._relay_cache[recipient_pubkey_hex]
            if time.time() < expiry:
                _LOGGER.debug(
                    "Using cached relays for recipient %s",
                    recipient_pubkey_hex,
                )
                return relays

        # Discover from relays
        filter_obj = Filter().kind(KIND_INBOX_RELAYS).author(recipient_pubkey_hex).limit(1)

        events = await self._connect_and_query(filter_obj)

        if not events:
            _LOGGER.info("No kind 10050 event found for recipient %s", recipient_pubkey_hex)
            return []

        event = events[0]
        relays = []
        for tag in event.tags():
            if tag.as_vec() and tag.as_vec()[0] == KIND_10050_RELAY_TAG:
                if len(tag.as_vec()) > 1:
                    relay = tag.as_vec()[1]
                    if relay.startswith(("wss://", "ws://")):
                        relays.append(relay)

        if relays:
            _LOGGER.debug(
                "Found %d messaging relay(s) for recipient %s: %s",
                len(relays),
                recipient_pubkey_hex,
                relays,
            )
            # Cache the result
            import time
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
        """Publish kind 0 metadata event for the topic."""
        content = f'{{"name": "{topic_name}", "display_name": "{topic_name}"}}'

        builder = UnsignedEvent(KIND_METADATA, content)
        event = await builder.sign_with_keys(self._keys)

        pool = RelayPool()
        for relay_url in target_relays:
            pool.add_relay(relay_url)

        try:
            await asyncio.wait_for(pool.connect(), timeout=timeout_sec)
        except asyncio.TimeoutError:
            _LOGGER.warning("Timed out connecting to metadata relays")
            return
        except Exception as e:
            _LOGGER.warning("Failed to connect to metadata relays: %s", e)
            return

        publish_tasks = []
        for relay_url in target_relays:
            task = asyncio.create_task(
                pool.send_event(event, timeout=timeout_sec)
            )
            publish_tasks.append(task)

        if publish_tasks:
            done, _ = await asyncio.wait(
                publish_tasks, timeout=timeout_sec * len(target_relays)
            )
            for task in publish_tasks:
                if task in done:
                    try:
                        await task
                    except Exception as e:
                        _LOGGER.warning("Failed to publish metadata event: %s", e)
                else:
                    _LOGGER.warning("Metadata publish task timed out")

        try:
            await pool.disconnect()
        except Exception:
            pass

    async def send_encrypted_dm(
        self,
        recipient_pubkey_hex: str,
        message: str,
        recipient_relays: list[str],
        timeout_sec: float = PUBLISH_TIMEOUT_SEC,
    ) -> None:
        """Send NIP-17 encrypted direct message using NIP-59 and NIP-44."""
        if not recipient_relays:
            _LOGGER.info(
                "No messaging relays for recipient %s, skipping DM send",
                recipient_pubkey_hex,
            )
            return

        recipient_keys = Keys.parse(recipient_pubkey_hex)

        rumor = UnsignedEvent(KIND_RUMOR, message)
        rumor.add_tag(Tag.parse(["p", recipient_pubkey_hex]))
        rumor_content = rumor.content()
        rumor_tags = rumor.tags()

        seal = await GiftSeal.create_with_keys(self._keys, rumor_content, rumor_tags)

        gift_wrap = await GiftWrap.from_seal(
            self._keys, recipient_keys.public_key(), seal
        )
        gift_wrap_event = await gift_wrap.sign_with_keys(self._keys)

        pool = RelayPool()
        for relay_url in recipient_relays:
            pool.add_relay(relay_url)

        try:
            await asyncio.wait_for(pool.connect(), timeout=timeout_sec)
        except asyncio.TimeoutError:
            _LOGGER.warning("Timed out connecting to recipient relays")
            return
        except Exception as e:
            _LOGGER.warning("Failed to connect to recipient relays: %s", e)
            return

        publish_tasks = []
        for relay_url in recipient_relays:
            task = asyncio.create_task(
                pool.send_event(gift_wrap_event, timeout=timeout_sec)
            )
            publish_tasks.append(task)

        if publish_tasks:
            done, _ = await asyncio.wait(
                publish_tasks, timeout=timeout_sec * len(recipient_relays)
            )
            for task in publish_tasks:
                if task in done:
                    try:
                        await task
                    except Exception as e:
                        _LOGGER.warning("Failed to send gift wrap to relay: %s", e)
                else:
                    _LOGGER.warning("Gift wrap send task timed out")

        try:
            await pool.disconnect()
        except Exception:
            pass


async def generate_nostr_keypair() -> tuple[str, str]:
    """Generate a new Nostr keypair.

    Returns (private_key_hex, public_key_hex).
    """
    keys = Keys.generate()
    return keys.secret_key().to_hex(), keys.public_key().to_hex()


def decode_npub_to_hex(npub: str) -> str:
    """Decode a npub string to a hex public key."""
    keys = Keys.parse(npub)
    return keys.public_key().to_hex()
