from fastapi import params
import requests
from time import sleep

BASE_URL = "https://api.smartrecruiters.com/v1"


def get_jobs(company_slug: str, keyword: str = "", city: str = "", max_jobs: int = 200):
    jobs = []
    offset = 0
    limit = 100

    while True:
        url = f"{BASE_URL}/companies/{company_slug}/postings"
        params = {
            "offset": offset,
            "limit": limit,
        }
        #if keyword:
        #    params["q"] = keyword
        #if city:
        #    params["city"] = city

        print("URL =", url)
        print("PARAMS =", params)

        response = requests.get(
            url,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        content = data.get("content", [])

        if not content:
            break

        remaining = max_jobs - len(jobs)
        jobs.extend(content[:remaining])

        print(
            f"[{company_slug}] fetched {len(jobs)} / {data.get('totalFound', '?')}"
        )

        if len(content) < limit or len(jobs) >= max_jobs:
            break

        offset += limit
        sleep(0.2)

    return jobs


def get_job_details(company_slug: str, posting_id: str):
    url = (
        f"{BASE_URL}/companies/{company_slug}/postings/{posting_id}"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    company_slug = "Visa"

    jobs = get_jobs(company_slug)

    print(f"\nTotal jobs: {len(jobs)}")

    if jobs:
        first_job = jobs[0]

        details = get_job_details(
            company_slug,
            first_job["id"]
        )

        print("\nTitle:", details.get("name"))
        print("Location:", details.get("location", {}).get("city"))
