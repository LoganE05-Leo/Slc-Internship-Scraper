#!/usr/bin/env python3
"""Detect each company's ATS by following its careers_url and looking for
known ATS URL/HTML signatures. Writes config/companies.resolved.yaml.

Run as: python detect_ats.py
"""
import re
import sys
from pathlib import Path

import requests
import yaml

COMPANIES_PATH = Path("config/companies.yaml")
RESOLVED_PATH = Path("config/companies.resolved.yaml")
TIMEOUT = 20
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; slc-internship-scraper/1.0)"}

# Greenhouse's embed snippet is `boards.greenhouse.io/embed/job_board?for=TOKEN`.
# Check that pattern first -- otherwise the generic path-token regex below
# matches the literal word "embed" as the token.
GREENHOUSE_EMBED_RE = re.compile(
    r"boards\.greenhouse\.io/embed/job_board\?(?:[^\"'\s]*&)?for=([\w-]+)", re.IGNORECASE
)

SIGNATURES = [
    ("greenhouse", re.compile(r"(?:job-)?boards\.greenhouse\.io/(?!embed\b)([\w-]+)", re.IGNORECASE)),
    ("lever", re.compile(r"jobs\.lever\.co/([\w-]+)", re.IGNORECASE)),
    ("ashby", re.compile(r"jobs\.ashbyhq\.com/([\w-]+)", re.IGNORECASE)),
    ("smartrecruiters", re.compile(r"jobs\.smartrecruiters\.com/([\w-]+)", re.IGNORECASE)),
    ("workable", re.compile(r"apply\.workable\.com/([\w-]+)", re.IGNORECASE)),
]
WORKDAY_RE = re.compile(
    r"([\w-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[\w-]+/)?([\w-]+)", re.IGNORECASE
)


def detect(haystack: str):
    embed_match = GREENHOUSE_EMBED_RE.search(haystack)
    if embed_match:
        return {"ats": "greenhouse", "token": embed_match.group(1)}
    for ats, pattern in SIGNATURES:
        match = pattern.search(haystack)
        if match:
            return {"ats": ats, "token": match.group(1)}
    match = WORKDAY_RE.search(haystack)
    if match:
        return {"ats": "workday", "tenant": match.group(1), "dc": match.group(2), "site": match.group(3)}
    return None


def resolve_company(company: dict) -> dict:
    resolved = dict(company)
    careers_url = company.get("careers_url", "")

    if company.get("ats") and company.get("ats") != "auto":
        return resolved

    if not careers_url:
        resolved["ats"] = "unknown"
        return resolved

    try:
        resp = requests.get(careers_url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
        haystack = resp.url + "\n" + resp.text
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] {company.get('name')}: fetch failed: {exc}", file=sys.stderr)
        resolved["ats"] = "unknown"
        return resolved

    match = detect(haystack)
    resolved["source_url"] = resp.url
    if match:
        resolved.update(match)
        print(f"  -> {company.get('name')}: {match.get('ats')}")
    else:
        resolved["ats"] = "unknown"
        print(f"  -> {company.get('name')}: unknown (falling back to generic HTML)")
    return resolved


def main() -> None:
    with COMPANIES_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    companies = data.get("companies", [])

    resolved_companies = []
    for company in companies:
        print(f"Detecting ATS for {company.get('name')}...")
        resolved_companies.append(resolve_company(company))

    with RESOLVED_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump({"companies": resolved_companies}, f, sort_keys=False, allow_unicode=True)

    known = sum(1 for c in resolved_companies if c.get("ats") not in (None, "unknown", "auto"))
    print(f"\nWrote {RESOLVED_PATH} ({known}/{len(resolved_companies)} ATS resolved)")


if __name__ == "__main__":
    main()
