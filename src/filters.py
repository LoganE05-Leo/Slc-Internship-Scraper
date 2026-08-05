"""Filtering and tagging logic for internship postings."""
import os
import re

INTERN_RE = re.compile(r"\bintern(?:ship|s)?\b|\bco-?ops?\b", re.IGNORECASE)
FALL_2026_RE = re.compile(
    r"\b(?:fall|autumn)\s+2026\b|\b2026\s+(?:fall|autumn)\b", re.IGNORECASE
)
YEAR_2026_RE = re.compile(r"\b2026\b")

DEFAULT_LOCATION_KEYWORDS = [
    "salt lake city",
    "sandy",
    "draper",
    "lehi",
    "murray",
    "south jordan",
    "west valley",
    "cottonwood heights",
    "midvale",
    "west jordan",
    "remote",
]


def is_internship(text: str) -> bool:
    return bool(INTERN_RE.search(text or ""))


def is_fall_2026(text: str) -> bool:
    return bool(FALL_2026_RE.search(text or ""))


def is_year_2026(text: str) -> bool:
    return bool(YEAR_2026_RE.search(text or ""))


def tag_posting(posting: dict) -> list:
    """Return tags for a posting based on its title + description."""
    text = f"{posting.get('title', '')} {posting.get('description', '')}"
    tags = []
    if is_fall_2026(text):
        tags.append("fall-2026")
    elif is_year_2026(text):
        tags.append("2026")
    if is_internship(text):
        tags.append("internship")
    return tags


def location_keywords() -> list:
    raw = os.environ.get("LOCATION_KEYWORDS")
    if raw:
        return [k.strip().lower() for k in raw.split(",") if k.strip()]
    return DEFAULT_LOCATION_KEYWORDS


def location_matches(location: str) -> bool:
    """Unknown/empty locations are kept; otherwise must contain a keyword."""
    if not location or not location.strip():
        return True
    loc = location.lower()
    return any(keyword in loc for keyword in location_keywords())


def filter_postings(postings: list) -> list:
    """Apply intern-keyword, FILTER_MODE, and location filters.

    FILTER_MODE (env var, default "internship"):
      - "internship": keep every internship/co-op match (star Fall-2026 ones later).
      - "fall2026": keep only postings explicitly mentioning Fall/Autumn 2026.
      - "year2026": keep postings mentioning 2026 in any form.

    Kept as "keep-all" by default because ATS list endpoints frequently omit
    full descriptions, so a strict season filter would silently drop real
    postings that just don't mention the season in the title.
    """
    mode = os.environ.get("FILTER_MODE", "internship").lower()
    result = []
    for posting in postings:
        text = f"{posting.get('title', '')} {posting.get('description', '')}"
        if not is_internship(text):
            continue

        tags = tag_posting(posting)
        posting["tags"] = tags

        if mode == "fall2026" and "fall-2026" not in tags:
            continue
        if mode == "year2026" and not is_year_2026(text):
            continue

        if not location_matches(posting.get("location", "")):
            continue

        result.append(posting)
    return result
