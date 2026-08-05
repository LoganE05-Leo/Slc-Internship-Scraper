"""Markdown report generation. Fall-2026 postings are starred and listed first."""
from datetime import datetime, timezone


def build_report(new_postings: list) -> str:
    lines = [
        "# SLC Internship Scraper - Latest Run",
        "",
        f"_Generated: {datetime.now(timezone.utc).isoformat()}_",
        "",
    ]

    if not new_postings:
        lines.append("No new postings found this run.")
        return "\n".join(lines) + "\n"

    fall = [p for p in new_postings if "fall-2026" in p.get("tags", [])]
    others = [p for p in new_postings if "fall-2026" not in p.get("tags", [])]
    fall.sort(key=lambda p: (p.get("company", ""), p.get("title", "")))
    others.sort(key=lambda p: (p.get("company", ""), p.get("title", "")))

    lines.append(f"**{len(new_postings)} new posting(s)** -- {len(fall)} Fall 2026 (starred)")
    lines.append("")

    for posting in fall:
        lines.append(_format_line(posting, starred=True))
    for posting in others:
        lines.append(_format_line(posting, starred=False))

    lines.append("")
    return "\n".join(lines) + "\n"


def _format_line(posting: dict, starred: bool) -> str:
    star = "* " if starred else ""
    location = posting.get("location") or "Unknown location"
    title = posting.get("title", "")
    url = posting.get("url", "")
    company = posting.get("company", "")
    source = posting.get("source", "")
    return f"- {star}**{company}** -- [{title}]({url}) -- {location} ({source})"
