import google.generativeai as genai
from docx import Document
from pypdf import PdfReader
import sys
import json
import os
import re

GEMINI_API_KEY = "AIzaSyCaoabwu703HwQ8RbprLW347-Xe5m9qlCw"

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


def load_template():
    docx_path = "templates/base_letter.docx"
    pdf_path = "templates/base_letter.pdf"

    if os.path.exists(docx_path):
        doc = Document(docx_path)
        return "\n".join(
            p.text for p in doc.paragraphs
            if p.text.strip()
        )

    if os.path.exists(pdf_path):
        reader = PdfReader(pdf_path)
        txt = ""

        for page in reader.pages:
            t = page.extract_text()
            if t:
                txt += t + "\n"

        return txt

    raise Exception(
        "Ajoute templates/base_letter.docx ou pdf"
    )


def clean_text(text):
    text = re.sub(r"\*\*", "", text)
    text = re.sub(r"\*", "", text)
    text = text.replace("[Date du jour, ex: 11 juin 2024]", "")
    return text.strip()


def generate_letter(job_description, company_description):

    template = load_template()

    prompt = f"""
Tu es un correcteur de lettres de motivation.

MISSION :
Tu dois modifier UNIQUEMENT les parties de la lettre
qui ne correspondent pas au poste.

INTERDICTIONS :
- ne pas réécrire toute la lettre
- ne pas changer la structure
- ne pas changer le style
- ne pas changer les paragraphes personnels
- ne pas ajouter de texte
- ne pas inventer
- ne pas mettre de markdown
- pas d'astérisques
- garder exactement la mise en page

Tu modifies seulement :
1. l'objet
2. le paragraphe "Ce qui m'intéresse..."
3. éventuellement 1 phrase technique si nécessaire

Le reste doit rester IDENTIQUE.

LETTRE DE BASE :
{template}

DESCRIPTION POSTE :
{job_description}

DESCRIPTION ENTREPRISE :
{company_description}
"""

    response = model.generate_content(prompt)

    return clean_text(response.text)


if __name__ == "__main__":

    job_description = sys.argv[1]
    company_description = sys.argv[2]

    letter = generate_letter(
        job_description,
        company_description
    )

    with open(
        "generated_letter.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            {"letter": letter},
            f,
            indent=4,
            ensure_ascii=False
        )

    print("Lettre générée")