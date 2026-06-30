
import json
import sys
import re
from google import genai
from dotenv import load_dotenv
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import get_api_key

load_dotenv()

API_KEY = get_api_key("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY manquante (.env ou variable système)")

client = genai.Client(api_key=API_KEY)

def extract_job_title(job_description: str):

    if not job_description:
        return "ce poste"

    lines = [
        line.strip()
        for line in job_description.split("\n")
        if line.strip()
    ]

    if len(lines) == 0:
        return "ce poste"

    first_line = lines[0]

    if len(first_line) < 120:
        return first_line

    patterns = [
        r"(alternant[e]?\s.*)",
        r"(développeur.*)",
        r"(software engineer.*)",
        r"(full.?stack.*)",
        r"(data engineer.*)",
        r"(chef de projet.*)",
    ]

    text = job_description.lower()

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return match.group(1).title()

    return "ce poste"

data = json.loads(sys.argv[1])

contact_name = data.get("contact_name", "")
company_name = data.get("company_name", "")
headline = data.get("headline", "")
company_description = data.get("company_description", "")
job_description = data.get("job_description", "")
motivation_letter = data.get("motivation_letter","")

job_title = extract_job_title(job_description)

prompt = f"""
Tu rédiges un message LinkedIn de candidature.

Informations sur le candidat :

{motivation_letter}

Informations sur le recruteur :

Nom :
{contact_name}

Entreprise :
{company_name}

Headline :
{headline}

Description entreprise :
{company_description}

Description du poste :
{job_description}

Règles :

- La lettre de motivation est la source principale d'information.
- Ne jamais inventer de diplôme.
- Ne jamais inventer d'expérience.
- Ne jamais inventer de compétences.
- Ne jamais supposer que le candidat possède déjà les prérequis du poste.
- Réutiliser uniquement les informations présentes dans la lettre.
- Message LinkedIn de 5 à 8 lignes.
- Ton naturel et professionnel.
- Mentionner le poste.
- Montrer un intérêt sincère.
- Proposer un échange.
- Pas de listes.
- Pas d'emojis.
- Terminer obligatoirement par :

Bien cordialement,
Mathys URBAN

- Répondre uniquement avec le message final.
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

message = response.text.strip()

with open(
    "generated_message.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        {
            "message": message
        },
        f,
        ensure_ascii=False,
        indent=2
    )

print(message)

