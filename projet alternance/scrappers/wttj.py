#!/usr/bin/env python3
"""
Scraper Welcome to the Jungle — sortie JSON sur stdout.
Usage: py wttj_jobs.py <keyword> [company_slugs_file]

- keyword        : mot-clé de filtrage (ex: "développeur alternance")
- company_slugs_file : chemin vers un fichier JSON contenant une liste de slugs
                       d'entreprises à scraper. Si absent, toutes les entreprises
                       de la liste_entreprises.json sont utilisées.

Sortie : liste de jobs JSON sur stdout.
"""

import sys
import json
import os
import time
import re

try:
    import httpx
except ImportError:
    print(json.dumps({"error": "httpx non installé. Faites : pip install httpx[http2]"}))
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPANIES_FILE = os.path.join(BASE_DIR, "wttj_companies.json")

ALGOLIA_HEADERS = {
    "User-Agent":             "Mozilla/5.0",
    "Accept":                 "*/*",
    "Referer":                "https://www.welcometothejungle.com/",
    "Origin":                 "https://www.welcometothejungle.com",
    "x-algolia-api-key":      "4bd8f6215d0cc52b26430765769e65a0",
    "x-algolia-application-id": "CSEKHVMS53",
    "content-type":           "application/x-www-form-urlencoded",
}

COMPANIES_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept":     "application/json",
    "Referer":    "https://www.welcometothejungle.com/",
    "Origin":     "https://www.welcometothejungle.com",
}

def normalize_keyword(kw: str) -> list[str]:
    """Retourne une liste de tokens en minuscule pour le filtrage."""
    return [t.lower().strip() for t in re.split(r"[\s,/]+", kw) if t.strip()]


def job_matches(job: dict, tokens: list[str]) -> bool:
    """Retourne True si au moins un token est présent dans le titre ou la description."""
    if not tokens:
        return True
    title = (job.get("name") or job.get("title") or "").lower()
    dept  = (job.get("department") or "").lower()
    text  = title + " " + dept
    return any(t in text for t in tokens)


def safe_post(client, url, data, retries=3):
    for i in range(retries):
        try:
            r = client.post(url, headers=ALGOLIA_HEADERS, data=data, timeout=30)
            if r.status_code == 200:
                return r
            print(f"[WARN] HTTP {r.status_code}", file=sys.stderr)
            time.sleep(2 * (i + 1))
        except httpx.ReadTimeout:
            print(f"[TIMEOUT] retry {i+1}", file=sys.stderr)
            time.sleep(2 * (i + 1))
        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            time.sleep(2)
    return None

def fetch_companies() -> list[dict]:
    """Télécharge et met en cache la liste de toutes les entreprises WTTJ."""
    if os.path.exists(COMPANIES_FILE):
        mtime = os.path.getmtime(COMPANIES_FILE)
        age_hours = (time.time() - mtime) / 3600
        if age_hours < 24:
            with open(COMPANIES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("companies", [])

    print("[INFO] Téléchargement de la liste des entreprises WTTJ…", file=sys.stderr)
    try:
        r = httpx.get(
            "https://api.welcometothejungle.com/api/v1/companies",
            params={"name": "*", "order_by": "name", "language": "fr",
                    "page": "1", "per_page": "10000"},
            headers=COMPANIES_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data.get("companies", [])
    except Exception as e:
        print(f"[ERROR] fetch_companies : {e}", file=sys.stderr)
        return []

def scrape_jobs(keyword: str, slugs: list[str] | None = None) -> list[dict]:
    tokens = normalize_keyword(keyword)
    companies = fetch_companies()

    if not companies:
        print("[!] Aucune entreprise disponible", file=sys.stderr)
        return []
    if slugs:
        slug_set = set(slugs)
        companies = [
            c for c in companies
            if c.get("path", "")[14:] in slug_set
        ]
    MAX_COMPANIES = 10

    if MAX_COMPANIES:
        companies = companies[:MAX_COMPANIES]

    print(
        f"[INFO] {len(companies)} entreprise(s) à scraper",
        file=sys.stderr
    )

    all_jobs = []

    with httpx.Client(http2=True) as client:

        for index, company in enumerate(companies, start=1):

            slug = company.get("path", "")[14:]

            if not slug:
                continue

            print(
                f"[INFO] [{index}/{len(companies)}] Scraping {slug}",
                file=sys.stderr
            )

            payload = (
                f'{{"requests":[{{'
                f'"indexName":"wttj_jobs_production_fr_published_at_desc",'
                f'"params":"filters=(\\"organization.slug\\":\\"{slug}\\")&hitsPerPage=50&page=0"'
                f'}}]}}'
            )

            try:
                resp = safe_post(
                    client,
                    "https://csekhvms53-dsn.algolia.net/1/indexes/*/queries",
                    payload,
                )

                if resp is None:
                    print(
                        f"[SKIP] {slug}",
                        file=sys.stderr
                    )
                    continue

                data = resp.json()

                hits = (
                    data
                    .get("results", [{}])[0]
                    .get("hits", [])
                )

                print(
                    f"[INFO] {slug}: {len(hits)} offre(s) brute(s)",
                    file=sys.stderr
                )

            except Exception as e:
                print(
                    f"[ERROR] {slug}: {e}",
                    file=sys.stderr
                )
                continue

            for hit in hits:

                if not job_matches(hit, tokens):
                    continue

                office = hit.get("office") or {}

                location = (
                    office.get("name")
                    or hit.get("city")
                    or ""
                )

                country = office.get("country_code") or ""

                if country and location:
                    location = f"{location}, {country}"

                contract_map = {
                    "full_time": "CDI",
                    "FULL_TIME": "CDI",
                    "part_time": "Temps partiel",
                    "internship": "Stage",
                    "freelance": "Freelance",
                    "apprenticeship": "Alternance",
                    "APPRENTICESHIP": "Alternance",
                    "temporary": "CDD",
                }

                contract_raw = (
                    hit.get("contract_type")
                    or hit.get("contract_type_key")
                    or ""
                )

                contract_label = contract_map.get(
                    contract_raw,
                    contract_raw
                )

                slug_job = (
                    hit.get("slug")
                    or hit.get("objectID")
                    or ""
                )

                url = (
                    f"https://www.welcometothejungle.com/fr/companies/{slug}/jobs/{slug_job}"
                    if slug_job
                    else f"https://www.welcometothejungle.com/fr/companies/{slug}/jobs"
                )

                all_jobs.append({
                    "title": hit.get("name")
                             or hit.get("title")
                             or "Offre sans titre",

                    "company": company.get("name")
                               or slug,

                    "location": location,

                    "url": url,

                    "description":
                        hit.get("description_plain")
                        or hit.get("description")
                        or "",

                    "source": "Welcome to the Jungle",

                    "type": "offre",

                    "contract":
                        [contract_label]
                        if contract_label
                        else [],

                    "remote":
                        hit.get("remote")
                        or "",

                    "created_at":
                        hit.get("published_at")
                        or hit.get("updated_at")
                        or "",
                })

            time.sleep(0.2)

    print(
        f"[INFO] {len(all_jobs)} offre(s) trouvée(s)",
        file=sys.stderr
    )

    return all_jobs

if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else ""

    slugs_file = sys.argv[2] if len(sys.argv) > 2 else None
    slugs = None
    if slugs_file and os.path.exists(slugs_file):
        try:
            with open(slugs_file, "r", encoding="utf-8") as f:
                slugs = json.load(f)
        except Exception:
            slugs = None

    results = scrape_jobs(keyword, slugs)
    print(json.dumps(results, ensure_ascii=False))