"""Seen-jobs dedup state: sha1(url) -> {company, title, url, first_seen, last_seen}."""
import hashlib
import json
import time
from pathlib import Path

SEEN_FILE = Path("data/seen_jobs.json")
PRUNE_DAYS = 60


def job_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def load_seen() -> dict:
    if SEEN_FILE.exists():
        with SEEN_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_seen(seen: dict) -> None:
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SEEN_FILE.open("w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2, sort_keys=True)


def prune(seen: dict) -> dict:
    cutoff = time.time() - PRUNE_DAYS * 86400
    return {jid: entry for jid, entry in seen.items() if entry.get("last_seen", 0) >= cutoff}


def split_new(postings: list, seen: dict):
    """Return (new_postings, updated_seen). Mutates posting dicts to add 'id'."""
    now = time.time()
    new_postings = []
    for posting in postings:
        jid = job_id(posting["url"])
        posting["id"] = jid
        if jid not in seen:
            new_postings.append(posting)
            seen[jid] = {
                "company": posting.get("company", ""),
                "title": posting.get("title", ""),
                "url": posting.get("url", ""),
                "first_seen": now,
                "last_seen": now,
            }
        else:
            seen[jid]["last_seen"] = now
    return new_postings, seen
