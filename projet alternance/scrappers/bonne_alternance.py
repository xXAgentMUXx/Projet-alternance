import requests
import json
import time
import sys
import os
from dotenv import load_dotenv

load_dotenv()

LAT    = 43.610476  
LON    = 3.87048
RADIUS = 30         

API_TOKEN = os.getenv("LBA_API_TOKEN")

if not API_TOKEN:
    raise ValueError("LBA_API_TOKEN manquant (.env ou variable système)")

CODES_ROME = [
    "M1805",  
    "M1855",  
    "M1825",  
    "M1834", 
    "M1861",  
    "E1210", 
    "E1405",  
    "M1865", 
    "M1877",  
    "M1886",  
    "M1887",  
    "M1803",  
    "M1802",  
    "M1806",  

    "E1104",  
    "E1205",  
]

DEV_KEYWORDS = [
    "développeur", "developpeur", "developer",
    "fullstack", "full stack", "full-stack",
    "frontend", "front-end", "front end",
    "backend",  "back-end",  "back end",
    "web", "mobile", "react", "angular", "vue",
    "node", "python", "java", "php", "django",
    "spring", "typescript", "javascript",
    "software", "ingénieur logiciel", "ingenieur logiciel",
    "informaticien", "programmeur", "apprenti", "alternant",
    "intégrateur", "integrateur",

    "chef de projet", "project manager", "scrum master",
    "product owner", "moa", "maîtrise d'ouvrage",
    "chef de projet si", "chef de projet informatique",
    "responsable informatique", "architecte si",

    "jeu vidéo", "jeu video", "game", "gaming",
    "unity", "unreal", "godot", "game design", "game designer",
    "game developer", "développeur jeu", "programmeur jeu",
    "gameplay", "moteur de jeu",
]

URL = "https://api.apprentissage.beta.gouv.fr/api/job/v1/search"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json",
}

def title_is_dev(title: str) -> bool:
    return any(kw in title.lower() for kw in DEV_KEYWORDS)


def flatten(val) -> str:
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        return val.get("label") or val.get("value") or ""
    return str(val) if val else ""


def parse_job(j: dict) -> dict:
    wp  = j.get("workplace", {}) or {}
    loc = wp.get("location", {}) or {}
    apl = j.get("apply", {}) or {}
    off = j.get("offer", {}) or {}
    pub = j.get("publication", {}) or {}
    ctr = j.get("contract", {}) or {}
    idf = j.get("identifier", {}) or {}

    return {
        "source":        idf.get("partner_label") or "offre_emploi",
        "title":         flatten(off.get("title") or ""),
        "company":       flatten(wp.get("name") or wp.get("brand") or wp.get("legal_name") or ""),
        "location":      flatten(loc.get("address") or wp.get("city") or ""),
        "url":           flatten(apl.get("url") or ""),
        "phone":         flatten(apl.get("phone") or ""),
        "description":   flatten(off.get("description") or "")[:300],
        "created_at":    flatten(pub.get("creation") or ""),
        "contract_type": ctr.get("type") or [],
        "remote":        flatten(ctr.get("remote") or ""),
        "is_delegated":  j.get("is_delegated", False),
    }


def parse_recruiter(r: dict) -> dict:
    wp  = r.get("workplace", {}) or {}
    loc = wp.get("location", {}) or {}
    apl = r.get("apply", {}) or {}
    dom = wp.get("domain", {}) or {}
    naf = dom.get("naf") or {}

    return {
        "source":      "candidature_spontanee",
        "title":       "",
        "company":     flatten(wp.get("name") or wp.get("brand") or wp.get("legal_name") or ""),
        "location":    flatten(loc.get("address") or ""),
        "url":         flatten(apl.get("url") or ""),
        "phone":       flatten(apl.get("phone") or ""),
        "description": flatten(wp.get("description") or "")[:300],
        "naf":         flatten(naf.get("label") if isinstance(naf, dict) else naf),
        "opco":        flatten(dom.get("opco") or ""),
        "size":        flatten(wp.get("size") or ""),
        "website":     flatten(wp.get("website") or ""),
        "siret":       flatten(wp.get("siret") or ""),
    }

def fetch(romes: list[str]) -> dict:
    try:
        r = requests.get(
            URL,
            params={
                "latitude":  LAT,
                "longitude": LON,
                "radius":    RADIUS,
                "romes":     ",".join(romes),
            },
            headers=HEADERS,
            timeout=60,
        )
        if r.status_code == 429:
            print("  [!] Rate limit — pause 30s")
            time.sleep(30)
            return fetch(romes)
        if r.status_code != 200:
            print(f"  [!] HTTP {r.status_code} : {r.text[:200]}")
            return {}
        return r.json()
    except Exception as e:
        print(f"  [!] Erreur : {e}")
        return {}


def debug_api():
    print("=== MODE DEBUG ===\n")
    r = requests.get(
        URL,
        params={
            "latitude":  LAT,
            "longitude": LON,
            "radius":    RADIUS,
            "romes":     ",".join(CODES_ROME),
        },
        headers=HEADERS,
        timeout=30,
    )
    print(f"Status : {r.status_code}")
    print(f"URL    : {r.url}\n")
    d = r.json()
    jobs  = d.get("jobs", [])
    recs  = d.get("recruiters", [])
    warns = d.get("warnings", [])

    print(f"jobs       : {len(jobs)}")
    print(f"recruiters : {len(recs)}")
    print(f"warnings   : {warns}\n")

    if jobs:
        print("── Premier job ──")
        print(json.dumps(jobs[0], indent=2, ensure_ascii=False)[:800])
    if recs:
        print("\n── Premier recruteur ──")
        print(json.dumps(recs[0], indent=2, ensure_ascii=False)[:600])



def scrape_lba():
    offres:       list[dict] = []
    candidatures: list[dict] = []
    seen_jobs: set[str] = set()
    seen_recs: set[str] = set()

    print(f"Recherche La Bonne Alternance — Montpellier {RADIUS}km")
    print(f"ROME : {', '.join(CODES_ROME)}")
    print("-" * 55)

    print(f"Appels ROME individuels ({len(CODES_ROME)} codes)...")

    for rome in CODES_ROME:
        print(f"  {rome}...", end=" ", flush=True)
        data = fetch([rome])
        raw_j = data.get("jobs",      []) or []
        raw_r = data.get("recruiters",[]) or []

        nb_j = nb_r = 0

        for j in raw_j:
            item = parse_job(j)
            if not title_is_dev(item["title"]):
                continue
            url = item["url"].strip()
            key = url if url else (
                item["title"].lower().strip()
                + "|"
                + item["company"].lower().strip()
            )
            if key and key not in seen_jobs:
                seen_jobs.add(key)
                offres.append(item)
                nb_j += 1

        for r in raw_r:
            item = parse_recruiter(r)
            key = item["siret"] or (item["company"] + item["location"])
            if key and key not in seen_recs:
                seen_recs.add(key)
                candidatures.append(item)
                nb_r += 1

        print(f"+{nb_j} offres | +{nb_r} recruteurs  (brut: {len(raw_j)}j {len(raw_r)}r)")
        time.sleep(1.2)  

    output = {
        "meta": {
            "location":         "Montpellier",
            "radius_km":        RADIUS,
            "romes":            CODES_ROME,
            "total_offres":     len(offres),
            "total_spontanees": len(candidatures),
            "total":            len(offres) + len(candidatures),
        },
        "offres_emploi":           offres,
        "candidatures_spontanees": candidatures,
    }
    filename = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "lba_montpellier_dev.json"
    )
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print("\n" + "-" * 55)
    print(f"Offres d'emploi         : {len(offres)}")
    print(f"Candidatures spontanées : {len(candidatures)}")
    print(f"Total                   : {len(offres) + len(candidatures)}")
    print(f"Fichier                 : {filename}")


if __name__ == "__main__":
    if "--debug" in sys.argv:
        debug_api()
    else:
        scrape_lba()

