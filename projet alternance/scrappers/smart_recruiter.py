import requests
import json
import os
from time import sleep

BASE_URL = "https://api.smartrecruiters.com/v1"

def load_prefs() -> dict:
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "auto_search_config.json"
    )
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_jobs(company_slug: str, keyword: str = "", city: str = "", max_jobs: int = 200):
    if not keyword or not city:
        prefs   = load_prefs()
        keyword = keyword or prefs.get("keyword") or ""
        city    = city    or prefs.get("city")    or ""

    jobs   = []
    offset = 0
    limit  = 100

    while True:
        url    = f"{BASE_URL}/companies/{company_slug}/postings"
        params = {"offset": offset, "limit": limit}
        if keyword:
            params["q"] = keyword
        if city:
            params["city"] = city

        print(f"[SmartRecruiters] {company_slug} — keyword='{keyword}' city='{city}'")
        print(f"  URL    : {url}")
        print(f"  PARAMS : {params}")

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data    = response.json()
        content = data.get("content", [])

        if not content:
            break

        remaining = max_jobs - len(jobs)
        jobs.extend(content[:remaining])

        print(f"  [{company_slug}] fetched {len(jobs)} / {data.get('totalFound', '?')}")

        if len(content) < limit or len(jobs) >= max_jobs:
            break

        offset += limit
        sleep(0.2)

    return jobs


def get_job_details(company_slug: str, posting_id: str):
    url      = f"{BASE_URL}/companies/{company_slug}/postings/{posting_id}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    company_slug = "Visa"
    jobs         = get_jobs(company_slug)
    print(f"\nTotal jobs: {len(jobs)}")
    if jobs:
        details = get_job_details(company_slug, jobs[0]["id"])
        print("Title:",    details.get("name"))
        print("Location:", details.get("location", {}).get("city"))