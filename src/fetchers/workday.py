"""Workday CXS jobs API fetcher (myworkdayjobs.com)."""
import re

import requests

TIMEOUT = 20
PAGE_SIZE = 20
MAX_OFFSET = 200  # safety cap so a huge board can't loop forever

WORKDAY_URL_RE = re.compile(
    r"https?://([\w-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[\w-]+/)?([\w-]+)",
    re.IGNORECASE,
)


def parse_workday_url(url: str):
    """Extract (tenant, dc, site) from a myworkdayjobs.com careers URL."""
    match = WORKDAY_URL_RE.search(url or "")
    if not match:
        return None
    return match.group(1), match.group(2), match.group(3)


def fetch(tenant: str, dc: str, site: str, company_name: str) -> list:
    url = f"https://{tenant}.{dc}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    postings = []
    offset = 0
    total = None

    while offset < MAX_OFFSET and (total is None or offset < total):
        body = {
            "appliedFacets": {},
            "limit": PAGE_SIZE,
            "offset": offset,
            "searchText": "intern",
        }
        resp = requests.post(url, json=body, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        total = data.get("total", 0)
        job_postings = data.get("jobPostings", [])
        if not job_postings:
            break

        for job in job_postings:
            path = job.get("externalPath", "")
            postings.append(
                {
                    "company": company_name,
                    "title": job.get("title", ""),
                    "location": job.get("locationsText", ""),
                    "url": f"https://{tenant}.{dc}.myworkdayjobs.com/{site}{path}",
                    "posted_at": job.get("postedOn"),
                    "source": "workday",
                    "description": "",
                }
            )
        offset += PAGE_SIZE

    return postings
