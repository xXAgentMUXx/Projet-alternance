import json
from jobspy import scrape_jobs

MAX_RESULTS = 200


def scrape_linkedin(keyword, city):

    print(f"Recherche LinkedIn : {keyword} à {city}")

    try:
        jobs = scrape_jobs(
            site_name=["linkedin"],
            search_term=keyword,
            location=city,
            results_wanted=MAX_RESULTS,
            linkedin_fetch_description=False,
            hours_old=720,
            verbose=2
        )

        final = []

        for _, row in jobs.iterrows():
            final.append({
                "title": row.get("title"),
                "company": row.get("company"),
                "location": row.get("location"),
                "url": row.get("job_url"),
                "description": row.get("description"),
                "source": "linkedin"
            })

        return final

    except Exception as e:
        print(e)
        return []


if __name__ == "__main__":

    keyword = input("Mot clé : ")
    city = input("Ville : ")

    jobs = scrape_linkedin(
        keyword,
        city
    )

    with open(
        "linkedin_jobs.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            jobs,
            f,
            indent=4,
            ensure_ascii=False
        )

    print("Total :", len(jobs))