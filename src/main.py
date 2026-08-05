"""Entry point: fetch postings from every company's ATS, filter, dedup, report, email.

Run as: python -m src.main
"""
import os
import sys
from pathlib import Path

from src.config import load_companies
from src.emailer import send_email
from src.fetchers import ashby, generic_html, greenhouse, lever, smartrecruiters, workable, workday
from src.filters import filter_postings
from src.report import build_report
from src.state import load_seen, prune, save_seen, split_new


def fetch_company(company: dict) -> list:
    """Fetch postings for one company. Never raises -- errors are logged and skipped
    so one bad company can't kill the whole run."""
    name = company.get("name", "unknown")
    ats = (company.get("ats") or "").lower()
    try:
        if ats == "greenhouse":
            return greenhouse.fetch(company["token"], name)
        if ats == "lever":
            return lever.fetch(company["token"], name)
        if ats == "ashby":
            return ashby.fetch(company["token"], name)
        if ats == "smartrecruiters":
            return smartrecruiters.fetch(company["token"], name)
        if ats == "workable":
            return workable.fetch(company["token"], name)
        if ats == "workday":
            return workday.fetch(company["tenant"], company["dc"], company["site"], name)

        careers_url = company.get("careers_url") or company.get("source_url")
        if not careers_url:
            return []
        return generic_html.fetch(careers_url, name)
    except Exception as exc:  # noqa: BLE001 - deliberately broad, see docstring
        print(f"[warn] {name}: fetch failed (ats={ats or 'generic'}): {exc}", file=sys.stderr)
        return []


def main() -> None:
    companies = load_companies()
    print(f"Loaded {len(companies)} companies")

    all_postings = []
    for company in companies:
        postings = fetch_company(company)
        all_postings.extend(postings)
    print(f"Fetched {len(all_postings)} raw postings")

    matched = filter_postings(all_postings)
    print(f"{len(matched)} postings matched filters")

    seen = prune(load_seen())
    new_postings, seen = split_new(matched, seen)
    save_seen(seen)
    print(f"{len(new_postings)} new postings since last run")

    report_md = build_report(new_postings)
    report_path = Path("reports/latest.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_md, encoding="utf-8")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(report_md + "\n")

    if new_postings:
        sent = send_email(f"SLC Internship Scraper: {len(new_postings)} new posting(s)", report_md)
        print("Email sent" if sent else "Email not sent (SMTP env vars not fully configured)")
    else:
        print("No new postings; skipping email")


if __name__ == "__main__":
    main()
