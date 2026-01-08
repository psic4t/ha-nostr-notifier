"""Utility functions for Nostr key generation and slug handling."""
from __future__ import annotations

import re
from typing import Final

# Based on bech32 encoding for npub (bech32 alphabet excludes 1, b, i, o)
NPUB_PATTERN: Final = re.compile(r"^npub1[02-9ac-hj-np-z]{58}$")
SLUG_PATTERN: Final = re.compile(r"^[a-z0-9_\-]+$")


def is_valid_npub(value: str) -> bool:
    """Check if a string is a valid npub."""
    return bool(NPUB_PATTERN.match(value.strip()))


def generate_topic_slug(topic_name: str, existing_slugs: list[str] | None = None) -> str:
    """Generate a stable topic slug from a topic name with collision handling.

    The slug is derived from topic name by:
    1. Converting to lowercase
    2. Replacing spaces with underscores
    3. Removing any characters that are not alphanumeric, underscore, or hyphen

    If the slug already exists in existing_slugs, auto-suffix with _2, _3, etc.
    """
    existing_slugs_set = set(existing_slugs) if existing_slugs else set()

    # Generate base slug
    base_slug = topic_name.lower().replace(" ", "_")
    base_slug = re.sub(r"[^a-z0-9_\-]", "", base_slug)

    if not base_slug:
        base_slug = "topic"

    # Handle collisions
    slug = base_slug
    counter = 2
    while slug in existing_slugs_set:
        slug = f"{base_slug}_{counter}"
        counter += 1

    return slug


def parse_recipients(text: str) -> list[str]:
    """Parse recipients from multiline text input.

    Returns list of valid, unique npub strings.
    """
    lines = text.strip().splitlines()
    recipients = set()

    for line in lines:
        npub = line.strip()
        if npub and is_valid_npub(npub):
            recipients.add(npub)

    return sorted(recipients)
