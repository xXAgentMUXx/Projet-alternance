import argparse
import json
import os
import sys

from database2 import clear_jobs, init_db, save_jobs
from scrapers.francetravail import scrape_francetravail
from scrapers.hellowork import scrape_hellowork


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(ROOT_DIR, "data")
DEFAULT_DB = os.path.join(DATA_FOLDER, "jobs.db")

AVAILABLE_SCRAPERS = {
    "hellowork": scrape_hellowork,
    "francetravail": scrape_francetravail,
}


def load_configuration():

    config = os.path.join(ROOT_DIR, "..", "auto_search_config.json")

    if not os.path.isfile(config):
        return {}

    try:
        with open(config, "r", encoding="utf-8") as stream:
            return json.load(stream)
    except Exception:
        return {}


def prepare_database(path):

    os.makedirs(os.path.dirname(path), exist_ok=True)


def execute_scrapers(keyword, location, contract, enabled_sources):

    collected = []

    for source_name in enabled_sources:

        scraper = AVAILABLE_SCRAPERS.get(source_name)

        if scraper is None:
            print(f"Source inconnue : {source_name}")
            continue

        try:

            print(
                f"[{source_name}] Recherche lancée "
                f"(keyword='{keyword}', location='{location}')",
                file=sys.stderr,
            )

            result = scraper(
                keyword=keyword,
                location=location,
                job_type=contract,
            )

            if result:
                collected.extend(result)

        except Exception as exc:

            print(
                f"Erreur sur {source_name} : {exc}",
                file=sys.stderr,
            )

    return collected


def build_parser():

    prefs = load_configuration()

    parser = argparse.ArgumentParser(
        description="Scraping d'offres d'emploi"
    )

    parser.add_argument(
        "--keyword",
        default=prefs.get("keyword", "cyber"),
        help="Mot-clé recherché",
    )

    parser.add_argument(
        "--location",
        default=prefs.get("city", "France"),
        help="Ville ou zone géographique",
    )

    parser.add_argument(
        "--job-type",
        default="",
        help="Type de contrat",
    )

    parser.add_argument(
        "--sources",
        nargs="+",
        default=list(AVAILABLE_SCRAPERS.keys()),
        choices=list(AVAILABLE_SCRAPERS.keys()),
        help="Liste des scrapers à exécuter",
    )

    parser.add_argument(
        "--db-path",
        default=DEFAULT_DB,
        help="Chemin de la base SQLite",
    )

    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Conserver les anciennes données",
    )

    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Afficher les résultats JSON",
    )

    return parser


def run():

    args = build_parser().parse_args()

    prepare_database(args.db_path)

    init_db(args.db_path)

    if not args.no_clear:
        clear_jobs(args.db_path)

    jobs = execute_scrapers(
        keyword=args.keyword,
        location=args.location,
        contract=args.job_type,
        enabled_sources=args.sources,
    )

    if jobs:
        save_jobs(jobs, args.db_path)

    print(
        f"Total des offres récupérées : {len(jobs)}",
        file=sys.stderr,
    )

    if args.print_json:
        print(
            json.dumps(
                jobs,
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    run()