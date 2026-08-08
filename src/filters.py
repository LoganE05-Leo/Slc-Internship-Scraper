"""Filtering and tagging logic for internship postings."""
import os
import re

# Title-level signal: a title match is trusted outright. Includes common
# finance-internship title conventions that don't contain "intern" at all.
TITLE_INTERN_RE = re.compile(
    r"\bintern(?:ship|s)?\b"
    r"|\bco-?ops?\b"
    r"|\bsummer\s+analysts?\b"
    r"|\bsummer\s+associates?\b"
    r"|\brotational\s+programs?\b",
    re.IGNORECASE,
)

# Backwards-compatible alias used for title/anchor-text matching where no
# separate description exists (e.g. the generic HTML fallback's link text).
INTERN_RE = TITLE_INTERN_RE

# Description-level fallback: only used when the title itself didn't match.
DESCRIPTION_INTERN_RE = re.compile(r"\bintern(?:ship|s)?\b|\bco-?ops?\b", re.IGNORECASE)

# Words that, found near an "intern(ship)" mention in a description, mean
# it's describing a *qualification* ("internship experience preferred")
# rather than the posting itself being an internship.
_DISQUALIFYING_WORDS = {"experience", "preferred", "required", "plus", "background"}
_CONTEXT_WINDOW = 4

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


def _is_disqualified_mention(text: str, match: re.Match) -> bool:
    start, end = match.span()
    before = re.findall(r"[A-Za-z]+", text[:start])[-_CONTEXT_WINDOW:]
    after = re.findall(r"[A-Za-z]+", text[end:])[:_CONTEXT_WINDOW]
    nearby = {w.lower() for w in before + after}
    return bool(nearby & _DISQUALIFYING_WORDS)


def is_internship_title(title: str) -> bool:
    return bool(TITLE_INTERN_RE.search(title or ""))


def is_internship_description(description: str) -> bool:
    """True if the description has an "intern(ship)"/"co-op" mention that
    isn't just describing a preferred qualification (e.g. "internship
    experience preferred" on an otherwise full-time role)."""
    text = description or ""
    return any(
        not _is_disqualified_mention(text, match)
        for match in DESCRIPTION_INTERN_RE.finditer(text)
    )


def is_internship(posting: dict) -> bool:
    """Title match wins outright. Description is only a fallback, so a
    generic title (e.g. "Paralegal") doesn't get pulled in just because its
    description prefers candidates with past internship experience."""
    if is_internship_title(posting.get("title", "")):
        return True
    return is_internship_description(posting.get("description", ""))


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
    if is_internship(posting):
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
        if not is_internship(posting):
            continue

        tags = tag_posting(posting)
        posting["tags"] = tags

        if mode == "fall2026" and "fall-2026" not in tags:
            continue
        if mode == "year2026":
            text = f"{posting.get('title', '')} {posting.get('description', '')}"
            if not is_year_2026(text):
                continue

        if not location_matches(posting.get("location", "")):
            continue

        result.append(posting)
    return result
