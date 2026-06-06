import json
import sys
import re
from google import genai

client = genai.Client(
    api_key="AIzaSyCaoabwu703HwQ8RbprLW347-Xe5m9qlCw"
)

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
company_description = data.get("company_description", "")
job_description = data.get("job_description", "")

job_title = extract_job_title(job_description)

prompt = f"""
Tu es un recruteur expérimenté.

Rédige un message LinkedIn de candidature personnalisé.

Informations :

Nom du contact :
{contact_name}

Entreprise :
{company_name}

Poste :
{job_title}

Description de l'entreprise :
{company_description}

Description du poste :
{job_description}

Contraintes :

- 6 à 10 lignes maximum
- ton professionnel et naturel
- mentionner le poste
- montrer un intérêt sincère
- proposer un échange
- ne jamais recopier le CV
- ne jamais inventer d'informations
- éviter les tournures typiques d'IA
- répondre uniquement avec le message final
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