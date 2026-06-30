import json
import os
from scrappers import scrape_jobs

MAX_RESULTS = 200


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

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


def scrape_indeed(keyword=None, city=None):
    if not keyword or not city:
        prefs   = load_prefs()
        keyword = keyword or prefs.get("keyword") or "alternance développeur"
        city    = city    or prefs.get("city")    or "Montpellier"

    print(f"[Indeed] Recherche : '{keyword}' à '{city}'")

    try:
        jobs = scrape_jobs(
            site_name=["indeed"],
            search_term=keyword,
            location=city,
            results_wanted=MAX_RESULTS,
            country_indeed="France",
            hours_old=720,
            verbose=2,
        )

        final = []
        for _, row in jobs.iterrows():
            final.append({
                "title":       row.get("title"),
                "company":     row.get("company"),
                "location":    row.get("location"),
                "url":         row.get("job_url"),
                "description": row.get("description"),
                "source":      "indeed",
            })

        print(f"[Indeed] {len(final)} offres trouvées")
        return final

    except Exception as e:
        print(f"[Indeed] Erreur : {e}")
        return []


if __name__ == "__main__":
    prefs   = load_prefs()
    keyword = prefs.get("keyword") or input("Mot clé : ")
    city    = prefs.get("city")    or input("Ville : ")

    jobs = scrape_indeed(keyword, city)

    output_path = os.path.join(BASE_DIR, "indeed_jobs.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=4, ensure_ascii=False)

    print("Total :", len(jobs))