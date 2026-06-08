import argparse
import json
import os

from scrapers.indeed import scrape_indeed
from scrapers.hellowork import scrape_hellowork
from scrapers.wtj import scrape_wtj
from scrapers.jobteaser import scrape_jobteaser
from scrapers.monster import scrape_monster
from scrapers.francetravail import scrape_francetravail
from utils.database import init_db, save_jobs, clear_jobs

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "jobs.db")

SCRAPERS = {
    "hellowork": scrape_hellowork,
    "francetravail": scrape_francetravail,
}


def ensure_data_dir(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)


def run_scrapers(keyword, location, job_type, sources=None):
    jobs = []
    selected = sources or list(SCRAPERS.keys())

    for source in selected:
        scraper = SCRAPERS.get(source)
        if scraper is None:
            print(f"Source inconnue : {source}")
            continue

        try:
            print(f"Lancement du scraper {source}...")
            jobs += scraper(keyword=keyword, location=location, job_type=job_type)
        except Exception as e:
            print(f"Erreur globale {source} : {e}")

    return jobs


def parse_args():
    parser = argparse.ArgumentParser(
        description="Lancer le scraping de jobs depuis la ligne de commande et enregistrer dans data/jobs.db"
    )

    parser.add_argument("--keyword", default="cyber", help="Mot-clé de recherche (par ex. cyber, alternance)")
    parser.add_argument("--location", default="France", help="Localisation de recherche")
    parser.add_argument("--job-type", default="", help="Type de contrat (par ex. Alternance, CDI)")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=list(SCRAPERS.keys()),
        default=list(SCRAPERS.keys()),
        help="Sources à scrapper (par défaut toutes)",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Ne pas vider la base de données avant l'insertion",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Afficher les résultats JSON après le scraping",
    )
    parser.add_argument(
        "--db-path",
        default=DB_PATH,
        help="Chemin vers le fichier SQLite de stockage",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    ensure_data_dir(args.db_path)
    init_db(args.db_path)

    if not args.no_clear:
        clear_jobs(args.db_path)

    jobs = run_scrapers(args.keyword, args.location, args.job_type, sources=args.sources)

    if jobs:
        save_jobs(jobs, args.db_path)

    print(f"Total des offres récupérées : {len(jobs)}")

    if args.print_json:
        print(json.dumps(jobs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
