import json
from jobspy import scrape_jobs

MAX_RESULTS = 200


def scrape_indeed(keyword, city):

    print(f"Recherche Indeed : {keyword} à {city}")

    try:
        jobs = scrape_jobs(
            site_name=["indeed"],
            search_term=keyword,
            location=city,
            results_wanted=MAX_RESULTS,
            country_indeed="France",
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
                "source": "indeed"
            })

        return final

    except Exception as e:
        print(e)
        return []


if __name__ == "__main__":

    keyword = input("Mot clé : ")
    city = input("Ville : ")

    jobs = scrape_indeed(
        keyword,
        city
    )

    with open(
        "indeed_jobs.json",
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