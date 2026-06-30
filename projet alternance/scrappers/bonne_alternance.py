import requests
import json
import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import get_api_key


DEFAULT_LAT    = 43.610476
DEFAULT_LON    = 3.87048
DEFAULT_CITY   = "Montpellier"
RADIUS         = 30


CITY_COORDS = {
    "montpellier":       (43.610476, 3.87048),
    "paris":             (48.8566,   2.3522),
    "lyon":              (45.7640,   4.8357),
    "marseille":         (43.2965,   5.3698),
    "toulouse":          (43.6047,   1.4442),
    "bordeaux":          (44.8378,   -0.5792),
    "nantes":            (47.2184,   -1.5536),
    "lille":             (50.6292,   3.0573),
    "nice":              (43.7102,   7.2620),
    "strasbourg":        (48.5734,   7.7521),
    "rennes":            (48.1173,   -1.6778),
    "grenoble":          (45.1885,   5.7245),
    "tours":             (47.3941,   0.6848),
    "dijon":             (47.3220,   5.0415),
    "angers":            (47.4784,   -0.5632),
    "reims":             (49.2583,   4.0317),
    "le mans":           (48.0061,   0.1996),
    "caen":              (49.1829,   -0.3707),
    "clermont-ferrand":  (45.7772,   3.0870),
    "brest":             (48.3904,   -4.4861),
    "perpignan":         (42.6986,   2.8956),
    "toulon":            (43.1242,   5.9280),
    "avignon":           (43.9493,   4.8055),
    "nancy":             (48.6921,   6.1844),
    "metz":              (49.1193,   6.1757),
    "rouen":             (49.4432,   1.0993),
    "saint-etienne":     (45.4397,   4.3872),
    "amiens":            (49.8942,   2.2957),
    "limoges":           (45.8336,   1.2611),
    "nimes":             (43.8367,   4.3601),
    "pau":               (43.2951,   -0.3708),
}


def city_to_coords(city: str):
    """Retourne (lat, lon) pour la ville donnée, ou les coords par défaut."""
    if not city:
        return DEFAULT_LAT, DEFAULT_LON
    key = city.strip().lower()
    key = (key.replace("é","e").replace("è","e").replace("ê","e")
              .replace("à","a").replace("â","a").replace("ç","c")
              .replace("î","i").replace("ô","o").replace("ù","u"))
    if key in CITY_COORDS:
        return CITY_COORDS[key]
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "limit": 1},
            headers={"User-Agent": "jobdash-scraper/1.0"},
            timeout=5,
        )
        if r.status_code == 200:
            results = r.json()
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        pass
    print(f"[LBA] Ville '{city}' inconnue, utilisation de Montpellier par défaut", file=sys.stderr)
    return DEFAULT_LAT, DEFAULT_LON


def load_prefs() -> dict:
    """Charge keyword et city depuis auto_search_config.json si disponible."""
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

API_TOKEN = get_api_key("LBA_API_KEY")

if not API_TOKEN:
    raise ValueError("LBA_API_TOKEN manquant (.env ou variable système)")

CODES_ROME = [
    "M1805", "M1855", "M1825", "M1834", "M1861",
    "E1210", "E1405", "M1865", "M1877", "M1886",
    "M1887", "M1803", "M1802", "M1806", "E1104", "E1205",
]

URL = "https://api.apprentissage.beta.gouv.fr/api/job/v1/search"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json",
}

def build_keyword_tokens(keyword: str) -> list[str]:
    """Découpe le keyword en tokens pour le filtrage des titres."""
    if not keyword:
        return []
    import re
    return [t.lower().strip() for t in re.split(r"[\s,/]+", keyword) if len(t.strip()) >= 3]


def title_matches(title: str, tokens: list[str]) -> bool:
    """Retourne True si le titre contient au moins un token du keyword."""
    if not tokens:
        return True
    t = title.lower()
    return any(tok in t for tok in tokens)

DEV_KEYWORDS = [
    "développeur", "developpeur", "developer",
    "fullstack", "full stack", "full-stack",
    "frontend", "front-end", "backend", "back-end",
    "web", "mobile", "react", "angular", "vue",
    "node", "python", "java", "php", "django",
    "spring", "typescript", "javascript",
    "software", "ingénieur logiciel", "informaticien",
    "programmeur", "apprenti", "alternant", "intégrateur",
    "chef de projet", "scrum master", "product owner",
    "jeu vidéo", "jeu video", "game", "gaming",
    "unity", "unreal", "godot", "game design",
]


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

def fetch(romes: list[str], lat: float, lon: float) -> dict:
    try:
        r = requests.get(
            URL,
            params={
                "latitude":  lat,
                "longitude": lon,
                "radius":    RADIUS,
                "romes":     ",".join(romes),
            },
            headers=HEADERS,
            timeout=60,
        )
        if r.status_code == 429:
            print("  [!] Rate limit — pause 30s", file=sys.stderr)
            time.sleep(30)
            return fetch(romes, lat, lon)
        if r.status_code != 200:
            print(f"  [!] HTTP {r.status_code} : {r.text[:200]}", file=sys.stderr)
            return {}
        return r.json()
    except Exception as e:
        print(f"  [!] Erreur : {e}", file=sys.stderr)
        return {}

def scrape_lba(keyword: str = "", city: str = ""):
    """
    Lance le scraping LBA.
    keyword et city peuvent être passés en argument (depuis run_scraper)
    ou seront lus depuis auto_search_config.json.
    """

    prefs = load_prefs()
    keyword = keyword or prefs.get("keyword") or ""
    city    = city    or prefs.get("city")    or DEFAULT_CITY

    lat, lon = city_to_coords(city)
    tokens   = build_keyword_tokens(keyword)

    offres:       list[dict] = []
    candidatures: list[dict] = []
    seen_jobs: set[str] = set()
    seen_recs: set[str] = set()

    print(f"[LBA] Recherche : '{keyword}' à '{city}' ({lat:.4f}, {lon:.4f}) — rayon {RADIUS}km", file=sys.stderr)
    print(f"[LBA] Codes ROME : {', '.join(CODES_ROME)}", file=sys.stderr)

    for rome in CODES_ROME:
        print(f"  {rome}...", end=" ", flush=True, file=sys.stderr)
        data  = fetch([rome], lat, lon)
        raw_j = data.get("jobs",       []) or []
        raw_r = data.get("recruiters", []) or []

        nb_j = nb_r = 0

        for j in raw_j:
            item = parse_job(j)
            if tokens:
                if not title_matches(item["title"], tokens):
                    continue
            else:
                if not title_is_dev(item["title"]):
                    continue

            url = item["url"].strip()
            key = url if url else (item["title"].lower().strip() + "|" + item["company"].lower().strip())
            if key and key not in seen_jobs:
                seen_jobs.add(key)
                offres.append(item)
                nb_j += 1

        for r in raw_r:
            item = parse_recruiter(r)
            key  = item["siret"] or (item["company"] + item["location"])
            if key and key not in seen_recs:
                seen_recs.add(key)
                candidatures.append(item)
                nb_r += 1

        print(f"+{nb_j} offres | +{nb_r} recruteurs  (brut: {len(raw_j)}j {len(raw_r)}r)", file=sys.stderr)
        time.sleep(1.2)

    output = {
        "meta": {
            "keyword":          keyword,
            "location":         city,
            "lat":              lat,
            "lon":              lon,
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
        os.path.dirname(os.path.abspath(__file__)), "..", "lba_montpellier_dev.json"
    )
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print(f"\n[LBA] Offres : {len(offres)} | Spontanées : {len(candidatures)} | Fichier : {filename}", file=sys.stderr)

    return output


def debug_api(lat=DEFAULT_LAT, lon=DEFAULT_LON):
    print("=== MODE DEBUG ===\n")
    r = requests.get(
        URL,
        params={"latitude": lat, "longitude": lon, "radius": RADIUS, "romes": ",".join(CODES_ROME)},
        headers=HEADERS,
        timeout=30,
    )
    print(f"Status : {r.status_code}")
    d = r.json()
    jobs = d.get("jobs", [])
    recs = d.get("recruiters", [])
    print(f"jobs: {len(jobs)} | recruiters: {len(recs)}")
    if jobs:
        print(json.dumps(jobs[0], indent=2, ensure_ascii=False)[:800])


if __name__ == "__main__":
    if "--debug" in sys.argv:
        debug_api()
    else:
        kw   = sys.argv[1] if len(sys.argv) > 1 else ""
        city = sys.argv[2] if len(sys.argv) > 2 else ""
        scrape_lba(kw, city)