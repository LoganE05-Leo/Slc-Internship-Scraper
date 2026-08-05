"""Greenhouse job board API fetcher."""
import requests

TIMEOUT = 20


def fetch(token: str, company_name: str) -> list:
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    postings = []
    for job in data.get("jobs", []):
        location = (job.get("location") or {}).get("name", "")
        postings.append(
            {
                "company": company_name,
                "title": job.get("title", ""),
                "location": location,
                "url": job.get("absolute_url", ""),
                "posted_at": job.get("updated_at") or job.get("first_published"),
                "source": "greenhouse",
                "description": job.get("content", ""),
            }
        )
    return postings
