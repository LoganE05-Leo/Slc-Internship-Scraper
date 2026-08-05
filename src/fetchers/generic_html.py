"""Best-effort BeautifulSoup fallback for companies with no known ATS.

Careers pages are frequently JavaScript-rendered, so this fetcher only
catches statically-linked internship postings. It's a fallback, not a
primary strategy -- see detect_ats.py, which tries hard to find a real
ATS API before main.py ever falls back to this module.
"""
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.filters import INTERN_RE

TIMEOUT = 20
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; slc-internship-scraper/1.0)"}


def fetch(careers_url: str, company_name: str) -> list:
    resp = requests.get(careers_url, timeout=TIMEOUT, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    postings = []
    seen_urls = set()
    for anchor in soup.find_all("a"):
        text = anchor.get_text(" ", strip=True)
        href = anchor.get("href")
        if not text or not href:
            continue
        if not INTERN_RE.search(text):
            continue

        full_url = urljoin(careers_url, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        postings.append(
            {
                "company": company_name,
                "title": text,
                "location": "",
                "url": full_url,
                "posted_at": None,
                "source": "generic",
                "description": "",
            }
        )
    return postings
