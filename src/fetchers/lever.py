"""Lever job postings API fetcher."""
import requests

TIMEOUT = 20


def fetch(token: str, company_name: str) -> list:
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    postings = []
    for job in data:
        categories = job.get("categories") or {}
        postings.append(
            {
                "company": company_name,
                "title": job.get("text", ""),
                "location": categories.get("location", ""),
                "url": job.get("hostedUrl", ""),
                "posted_at": job.get("createdAt"),
                "source": "lever",
                "description": job.get("descriptionPlain") or job.get("description", ""),
            }
        )
    return postings
