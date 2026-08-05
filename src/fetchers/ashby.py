"""Ashby job board API fetcher."""
import requests

TIMEOUT = 20


def fetch(token: str, company_name: str) -> list:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    postings = []
    for job in data.get("jobs", []):
        postings.append(
            {
                "company": company_name,
                "title": job.get("title", ""),
                "location": job.get("location", ""),
                "url": job.get("jobUrl") or job.get("applyUrl", ""),
                "posted_at": job.get("publishedAt"),
                "source": "ashby",
                "description": job.get("descriptionPlain", ""),
            }
        )
    return postings
