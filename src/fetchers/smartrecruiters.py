"""SmartRecruiters postings API fetcher."""
import requests

TIMEOUT = 20


def fetch(token: str, company_name: str) -> list:
    url = f"https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=100"
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    postings = []
    for job in data.get("content", []):
        loc = job.get("location") or {}
        location = ", ".join(filter(None, [loc.get("city"), loc.get("region")]))
        if not location:
            location = loc.get("country", "")
        job_url = job.get("ref") or f"https://jobs.smartrecruiters.com/{token}/{job.get('id', '')}"
        postings.append(
            {
                "company": company_name,
                "title": job.get("name", ""),
                "location": location,
                "url": job_url,
                "posted_at": job.get("releasedDate"),
                "source": "smartrecruiters",
                # The list endpoint doesn't return full descriptions.
                "description": "",
            }
        )
    return postings
