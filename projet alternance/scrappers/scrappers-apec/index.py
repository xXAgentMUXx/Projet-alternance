import json
import os
import sys
from warnings import warn
import common as jc
from scraping.jobs_apec import scraping_jobs_apec


CITY_TO_DEPARTMENT = {
    "paris": "75",
    "lyon": "69",
    "marseille": "13",
    "lille": "59",
    "bordeaux": "33",
    "nantes": "44",
    "nice": "06",
    "toulouse": "31",
    "rennes": "35",
    "strasbourg": "67",
    "montpellier": "34",
    "rouen": "76",
    "caen": "14",
    "grenoble": "38",
    "clermont-ferrand": "63",
    "clermont ferrand": "63",
    "nancy": "54",
    "dijon": "21",
    "metz": "57",
    "angers": "49",
    "reims": "51",
    "tours": "37",
    "orleans": "45",
    "avignon": "84",
    "tarbes": "65",
    "roubaix": "59",
    "saint-etienne": "42",
    "perpignan": "66",
    "toulon": "83",
    "brest": "29",
    "amiens": "80",
    "le havre": "76",
    "le mans": "72",
    "bayonne": "64",
    "montauban": "82",
}


def load_preferences():
    config_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "auto_search_config.json",
    )

    if not os.path.isfile(config_file):
        return {}

    try:
        with open(config_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def normalize_city(city):
    return (
        city.strip()
        .lower()
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ç", "c")
        .replace("î", "i")
        .replace("ô", "o")
        .replace("ù", "u")
    )


def get_department(city):
    if not city:
        return "34"

    return CITY_TO_DEPARTMENT.get(normalize_city(city), "34")


preferences = load_preferences()

contract_type = ""

if len(sys.argv) in (4, 5):

    keyword = sys.argv[1]
    city = sys.argv[2]
    department = sys.argv[3]

    if len(sys.argv) == 5:
        contract_type = sys.argv[4]

elif len(sys.argv) == 1:

    keyword = preferences.get("keyword", "alternance développeur")
    city = preferences.get("city", "Montpellier")
    department = get_department(city)

    print(
        f"[APEC] Paramètres chargés : '{keyword}' | {city} ({department})"
    )

else:

    warn(
        "Usage : python jobs_index.py \"keyword\" Ville CodeDept [TypeContrat]"
    )

    keyword = preferences.get("keyword", "alternance développeur")
    city = preferences.get("city", "Montpellier")
    department = get_department(city)

    print(
        f"[APEC] Paramètres par défaut : '{keyword}' | {city} ({department})"
    )


print(f"[APEC] Recherche : '{keyword}' à '{city}' ({department})")

jobs = []

scraper = scraping_jobs_apec(keyword, contract_type)
scraper.set_code_dpt(department)

jobs.extend(scraper.scrap_job())

print(jc.jprint(jobs))