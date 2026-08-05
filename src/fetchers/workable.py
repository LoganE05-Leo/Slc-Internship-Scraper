"""Workable widget API fetcher."""
import requests

TIMEOUT = 20


def fetch(token: str, company_name: str) -> list:
    url = f"https://apply.workable.com/api/v1/widget/accounts/{token}?details=true"
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    postings = []
    for job in data.get("jobs", []):
        location = job.get("location") or {}
        loc_parts = [location.get("city"), location.get("region")]
        loc_str = ", ".join(filter(None, loc_parts)) or location.get("country", "")
        shortcode = job.get("shortcode", "")
        job_url = job.get("url") or f"https://apply.workable.com/{token}/j/{shortcode}/"
        postings.append(
            {
                "company": company_name,
                "title": job.get("title", ""),
                "location": loc_str,
                "url": job_url,
                "posted_at": job.get("published_on") or job.get("created_at"),
                "source": "workable",
                "description": job.get("description", ""),
            }
        )
    return postings
