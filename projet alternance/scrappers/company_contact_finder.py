#!/usr/bin/env python3
"""
Recherche de contacts d'entreprise via l'API Google Gemini + Google Search.

Usage :
    py company_contact_finder.py "Capgemini"
    py company_contact_finder.py "Capgemini" --json
    py company_contact_finder.py "Capgemini" "SNCF" --output contacts.json

Nécessite :
    pip install -U google-genai

Clé API gratuite :
    https://aistudio.google.com/apikey

La clé doit être dans la variable d'environnement GEMINI_API_KEY.
"""

import sys
import os
import json
import argparse
import time
import difflib

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

CACHE_FILE = "company_cache.json"


def normalize_company_name(name: str) -> str:
    """
    Normalise un nom d'entreprise pour éviter
    les doublons et les fautes mineures.
    """

    return (
        name.lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace(".", "")
        .strip()
    )


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            cache,
            f,
            ensure_ascii=False,
            indent=2
        )


def get_cached_company(company_name: str):
    """
    Recherche exacte puis approximative.
    """

    cache = load_cache()

    normalized = normalize_company_name(company_name)
    if normalized in cache:
        print(f"Cache exact trouvé : {company_name}", file=sys.stderr)
        return cache[normalized]
    matches = difflib.get_close_matches(
        normalized,
        cache.keys(),
        n=1,
        cutoff=0.85
    )

    if matches:
        match = matches[0]

        print(f"Cache similaire trouvé : "f"{company_name} -> {match}", file=sys.stderr)

        return cache[match]

    return None


def save_company_to_cache(company_name: str, data: dict):
    cache = load_cache()

    normalized = normalize_company_name(company_name)

    cache[normalized] = data

    official_name = data.get("company_name")

    if official_name:
        cache[
            normalize_company_name(official_name)
        ] = data

    save_cache(cache)

SYSTEM_PROMPT = """Tu es un assistant spécialisé dans la recherche de contacts d'entreprises pour des candidats en recherche d'emploi.
Utilise Google Search pour trouver des informations précises et à jour.

Retourne UNIQUEMENT un objet JSON valide, sans texte avant ni après, avec cette structure exacte :
{
"company_name": "nom officiel de l'entreprise",
"website": "https://... (site officiel principal)",
"careers_url": "https://... (page carrières/emplois/recrutement)",
"contact_form_url": "https://... ou null si introuvable",
"hr_email": "email RH ou recrutement si public, ou null",
"hr_phone": "téléphone standard ou RH si public, ou null",
"linkedin_url": "https://linkedin.com/company/... ou null",
"headquarters": "Ville, Pays",
"sector": "secteur d'activité principal",
"description": "2 phrases max sur l'entreprise et son activité",
"contact_tips": [
"conseil concret et spécifique à cette entreprise pour la relance",
"deuxième conseil spécifique"
],
"confidence": "high | medium | low"
}

Règles :

- Ne fabrique JAMAIS de données. Si introuvable, mets null.
- Les URLs doivent être complètes et valides (https://).
- Les conseils doivent être spécifiques à cette entreprise.
"""

def find_company_contacts(company_name: str, api_key: str) -> dict:

    cached = get_cached_company(company_name)

    if cached:
        return cached

    client = genai.Client(api_key=api_key)

    prompt = (
        f"Recherche les informations de contact de l'entreprise "
        f"\"{company_name}\" pour un candidat qui souhaite relancer sa candidature. "
        f"Cherche : site officiel, page carrières, email ou formulaire RH, "
        f"téléphone, LinkedIn. Retourne uniquement le JSON demandé."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{SYSTEM_PROMPT}\n\n{prompt}",
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(
                    google_search=types.GoogleSearch()
                )
            ],
            temperature=0.1,
        ),
    )

    text = response.text.strip()

    if not text:
        raise ValueError("Gemini n'a retourné aucun texte.")

    try:
        result = json.loads(text)

    except json.JSONDecodeError:
        clean = text

        if "```" in clean:
            parts = clean.split("```")

            for part in parts:
                p = part.strip()

                if p.startswith("json"):
                    p = p[4:].strip()

                if p.startswith("{"):
                    clean = p
                    break

        start = clean.find("{")
        end = clean.rfind("}") + 1

        if start == -1 or end <= 0:
            raise ValueError(
                f"Aucun JSON trouvé dans la réponse : {clean[:300]}"
            )

        result = json.loads(clean[start:end])

    save_company_to_cache(company_name, result)

    return result

def print_result(result: dict):
    CONFIDENCE_LABELS = {
        "high": " Fiable",
        "medium": " Partiel",
        "low": " Incertain",
    }

    sep = "─" * 58

    print(f"\n{sep}")
    print(f"{result.get('company_name', 'Inconnu')}")

    if result.get("sector"):
        print(f"{result['sector']}")

    if result.get("headquarters"):
        print(f"{result['headquarters']}")

    confidence = CONFIDENCE_LABELS.get(
        result.get("confidence", "low"),
        ""
    )

    print(f"  Fiabilité : {confidence}")
    print(sep)

    if result.get("description"):
        print(f"\n  {result['description']}\n")

    fields = [
        ("", "Site web", "website"),
        ("", "Page carrières", "careers_url"),
        ("", "Formulaire contact", "contact_form_url"),
        ("", "Email RH", "hr_email"),
        ("", "Téléphone", "hr_phone"),
        ("", "LinkedIn", "linkedin_url"),
    ]

    print("  CONTACTS")
    print(f"  {'─' * 53}")

    found_any = False

    for icon, label, key in fields:
        value = result.get(key)

        if value:
            print(f"  {icon}  {label:<22} {value}")
            found_any = True

    if not found_any:
        print("  Aucun contact trouvé.")

    tips = result.get("contact_tips") or []

    if tips:
        print(f"\n  CONSEILS POUR LA RELANCE")
        print(f"  {'─' * 53}")

        for i, tip in enumerate(tips, 1):
            words = tip.split()

            buf = f"  {i}. "

            for word in words:
                if len(buf) + len(word) > 72:
                    print(buf)
                    buf = "     " + word + " "
                else:
                    buf += word + " "

            print(buf.rstrip())

    print(f"\n{sep}\n")


def get_api_key(cli_key: str | None) -> str:
    if cli_key:
        return cli_key

    return os.getenv("GEMINI_API_KEY", "")

def main():
    parser = argparse.ArgumentParser(
        description="Trouve les contacts d'une entreprise via Gemini + Google Search.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
py company_contact_finder.py "Capgemini"
py company_contact_finder.py "SNCF" --json
py company_contact_finder.py "Airbus" --output airbus_contacts.json
py company_contact_finder.py "Capgemini" "SNCF" "Airbus"
"""
    )

    parser.add_argument(
        "companies",
        nargs="+",
        help="Nom(s) d'entreprise à rechercher"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Afficher le résultat brut en JSON"
    )

    parser.add_argument(
        "--output",
        "-o",
        metavar="FICHIER.json",
        help="Sauvegarder les résultats dans un fichier JSON"
    )

    parser.add_argument(
    "--api-key",
    default=None,
    help="Clé API Gemini (optionnelle si .env ou variable d'environnement)"
    )   

    args = parser.parse_args()

    api_key = get_api_key(args.api_key)

    if not api_key:
        print("Clé API Gemini manquante.")
        print("https://aistudio.google.com/apikey")
        sys.exit(1)

    all_results = []
    errors = []

    for i, company in enumerate(args.companies):
        if i > 0:
            time.sleep(1)

        if not args.json:
            print(f'Recherche Gemini en cours pour "{company}"...')

        try:
            result = find_company_contacts(
                company,
                api_key
            )

            all_results.append(result)

            if not args.json:
                print_result(result)

        except Exception as e:
            errors.append({
                "company": company,
                "error": str(e)
            })

            if not args.json:
                print(f'Erreur pour "{company}" : {e}\n')

    if args.json:
        output = (
            all_results[0]
            if len(all_results) == 1
            else all_results
        )

        print(
            json.dumps(
                output,
                ensure_ascii=False,
                indent=2
            )
        )

    if args.output and all_results:
        data = {
            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),
            "results": all_results
        }

        if errors:
            data["errors"] = errors

        with open(
            args.output,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

        if not args.json:
            print(
                f"Résultats sauvegardés dans : {args.output}"
            )

    if errors and not args.json:
        print(
            f"{len(errors)} erreur(s) sur "
            f"{len(args.companies)} recherche(s)."
        )

    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
