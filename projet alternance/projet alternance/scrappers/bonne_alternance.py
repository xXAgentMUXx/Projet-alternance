import requests
import json

LAT = 43.6109
LON = 3.8763
RADIUS = 50
MAX_RESULTS = 1000

CODES_ROME = [
    "M1801",  # admin systèmes
    "M1802",  # support SI
    "M1803",  # direction SI
    "M1804",  # réseaux télécom
    "M1805",  # dev informatique
    "M1806",  # MOA / conseil
    "M1810"   # production SI
]

KEYWORDS = [
    "alternance",
    "développeur",
    "developpeur",
    "developer",
    "backend",
    "frontend",
    "fullstack",
    "full stack",
    "web",
    "software",
    "engineer",
    "ingénieur",
    "ingenieur",
    "java",
    "python",
    "react",
    "node"
]

API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJfaWQiOiI2YTA3MTc4YWQzNWYyMjY3MDdjZTVkMjYiLCJhcGlfa2V5IjoieXpSTi9sOGhqMy9JOUd3ZC9LUWpLWWlhd29kK1NucDNuczE0R2QvbUdIST0iLCJvcmdhbmlzYXRpb24iOm51bGwsImVtYWlsIjoidXJiYW4ubWF0aHlzQG91dGxvb2suY29tIiwiaXNzIjoiYXBpIiwiaWF0IjoxNzc4ODUxMDgyLCJleHAiOjE4MTAzODcwODJ9.iugq8pNHI_SQy6WO3_SyWkp1asz-7rkVT72B5DZFICo"
BASE_URL = "https://api.apprentissage.beta.gouv.fr/api/job/v1/search"


def title_match(title):
    """
    Vérifie si le titre contient
    un mot clé pertinent
    """
    title = title.lower()

    return any(
        keyword in title
        for keyword in KEYWORDS
    )


def fetch_jobs(page):
    params = {
        "latitude": LAT,
        "longitude": LON,
        "radius": RADIUS,
        "romes": ",".join(CODES_ROME),
        "page": page,
        "size": 50
    }

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json"
    }

    try:
        r = requests.get(
            BASE_URL,
            params=params,
            headers=headers,
            timeout=60
        )

        if r.status_code != 200:
            print("Erreur API:", r.text)
            return []

        data = r.json()

        return data.get("jobs", [])

    except Exception as e:
        print(e)
        return []


def scrape_lba():
    all_jobs = []
    page = 1

    print("Recherche La Bonne Alternance...")

    while True:

        print(f"page {page}")

        jobs = fetch_jobs(page)

        if not jobs:
            print("fin pagination")
            break

        for j in jobs:

            title = (
                j.get("offer", {}).get("title")
                or j.get("title")
                or ""
            )

            if not title_match(title):
                continue

            url = (
                j.get("apply", {}).get("url")
                or j.get("url")
            )

            company = (
                j.get("workplace", {}).get("name")
                or j.get("workplace", {}).get("legal_name")
                or "Entreprise inconnue"
            )

            location = (
                j.get("workplace", {})
                .get("location", {})
                .get("address")
                or j.get("workplace", {}).get("city")
                or "Non précisé"
            )

            all_jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "source": "Bonne Alternance"
            })

            if len(all_jobs) >= MAX_RESULTS:
                break

        if len(all_jobs) >= MAX_RESULTS:
            break

        page += 1

    # suppression doublons
    unique = {}

    for job in all_jobs:
        key = job["url"] or (
            job["title"] + job["company"]
        )
        unique[key] = job

    final = list(unique.values())

    with open(
        "bonne_alternance_jobs.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            final,
            f,
            indent=4,
            ensure_ascii=False
        )

    print("Total:", len(final))


if __name__ == "__main__":
    scrape_lba()