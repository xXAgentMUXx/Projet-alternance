from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from docx import Document
from pypdf import PdfReader
import subprocess
import json
import os
import hashlib


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    keyword: str
    city: str


# ─────────────────────────────────────────────
# Chemins
# ─────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

JSON_FILES = {
    "linkedin":         os.path.join(BASE_DIR, "linkedin_jobs.json"),
    "indeed":           os.path.join(BASE_DIR, "indeed_jobs.json"),
    "meteojob":         os.path.join(BASE_DIR, "meteojob_jobs.json"),
    "bonne_alternance": os.path.join(BASE_DIR, "lba_montpellier_dev.json"),
}

# Fichier qui persiste les jobs déjà vus (pour détecter les nouveaux)
SEEN_JOBS_FILE = os.path.join(BASE_DIR, "seen_jobs.json")


# ─────────────────────────────────────────────
# Système "New" — détection nouveaux jobs
# ─────────────────────────────────────────────

def job_fingerprint(job: dict) -> str:
    """
    Génère une clé unique pour un job.
    Basée sur url si disponible, sinon titre+company.
    """
    url = (job.get("url") or "").strip()
    if url:
        return hashlib.md5(url.encode()).hexdigest()
    key = (
        (job.get("title") or "").lower().strip()
        + "|"
        + (job.get("company") or "").lower().strip()
    )
    return hashlib.md5(key.encode()).hexdigest()


def load_seen_jobs() -> dict:
    """Charge le fichier des jobs déjà vus {fingerprint: platform}."""
    if os.path.exists(SEEN_JOBS_FILE):
        try:
            with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_seen_jobs(seen: dict):
    """Sauvegarde le fichier des jobs déjà vus."""
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2, ensure_ascii=False)


def mark_new_jobs(jobs: list, platform: str) -> list:
    """
    Ajoute le champ 'is_new': True/False à chaque job.
    Met à jour le fichier seen_jobs.json.
    """
    seen = load_seen_jobs()
    result = []
    updated = False

    for job in jobs:
        fp = job_fingerprint(job)
        if fp not in seen:
            seen[fp] = platform
            job["is_new"] = True
            updated = True
        else:
            job["is_new"] = False
        result.append(job)

    if updated:
        save_seen_jobs(seen)

    return result


# ─────────────────────────────────────────────
# Extraction fichiers template
# ─────────────────────────────────────────────

def extract_docx(path):
    doc = Document(path)
    return "\n".join(
        p.text for p in doc.paragraphs
        if p.text.strip()
    )


def extract_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        txt = page.extract_text()
        if txt:
            text += txt + "\n"
    return text


# ─────────────────────────────────────────────
# Scraper runner
# ─────────────────────────────────────────────

def run_scraper(script_name, keyword, city):
    try:
        if script_name == "linkedin":
            script_path = os.path.join(
                BASE_DIR, "scrappers", "JobSpy-main", "linkedin_jobs.py"
            )
        elif script_name == "indeed":
            script_path = os.path.join(
                BASE_DIR, "scrappers", "JobSpy-main", "indeed_jobs.py"
            )
        else:
            script_path = os.path.join(
                BASE_DIR, "scrappers", f"{script_name}.py"
            )

        json_file = JSON_FILES[script_name]

        result = subprocess.run(
            ["py", script_path],
            input=f"{keyword}\n{city}",
            text=True,
            capture_output=True,
            cwd=BASE_DIR,
        )

        print(result.stdout)
        if result.stderr:
            print("[stderr]", result.stderr[:500])

        if not os.path.exists(json_file):
            print(f"[!] Fichier introuvable : {json_file}")
            return []

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Normalisation LBA
        if script_name == "bonne_alternance":
            jobs = normalize_lba(data)
        else:
            jobs = data

        # Marquage "New"
        return mark_new_jobs(jobs, script_name)

    except Exception as e:
        print(f"[!] Erreur run_scraper({script_name}) : {e}")
        return {"error": str(e)}


# ─────────────────────────────────────────────
# Normalisation LBA
# ─────────────────────────────────────────────

def normalize_lba(data: dict | list) -> list:
    if isinstance(data, list):
        return data

    result = []

    for job in data.get("offres_emploi", []):
        result.append({
            "title":       job.get("title", ""),
            "company":     job.get("company", ""),
            "location":    job.get("location", ""),
            "url":         job.get("url", ""),
            "phone":       job.get("phone", ""),
            "description": job.get("description", ""),
            "source":      job.get("source", "offre_emploi"),
            "type":        "offre",
            "contract":    job.get("contract_type", []),
            "remote":      job.get("remote", ""),
            "created_at":  job.get("created_at", ""),
        })

    for rec in data.get("candidatures_spontanees", []):
        result.append({
            "title":       "Candidature spontanée",
            "company":     rec.get("company", ""),
            "location":    rec.get("location", ""),
            "url":         rec.get("url", ""),
            "phone":       rec.get("phone", ""),
            "description": rec.get("description", "") or rec.get("naf", ""),
            "source":      "recruteur_lba",
            "type":        "spontanee",
            "website":     rec.get("website", ""),
            "size":        rec.get("size", ""),
            "siret":       rec.get("siret", ""),
            "opco":        rec.get("opco", ""),
        })

    return result


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.post("/search-all")
def search_all(data: SearchRequest):
    return {
        "LinkedIn":         run_scraper("linkedin",         data.keyword, data.city),
        "Indeed":           run_scraper("indeed",           data.keyword, data.city),
        "Meteojob":         run_scraper("meteojob",         data.keyword, data.city),
        "Bonne Alternance": run_scraper("bonne_alternance", data.keyword, data.city),
    }


@app.post("/search/LinkedIn")
def search_linkedin(data: SearchRequest):
    return {"jobs": run_scraper("linkedin", data.keyword, data.city)}


@app.post("/search/Indeed")
def search_indeed(data: SearchRequest):
    return {"jobs": run_scraper("indeed", data.keyword, data.city)}


@app.post("/search/Meteojob")
def search_meteojob(data: SearchRequest):
    return {"jobs": run_scraper("meteojob", data.keyword, data.city)}


@app.post("/search/Bonne Alternance")
def search_bonne_alternance(data: SearchRequest):
    return {"jobs": run_scraper("bonne_alternance", data.keyword, data.city)}


@app.post("/generate-letter")
async def generate_letter(
    job_description:     str        = Form(...),
    company_description: str        = Form(...),
    template_file:       UploadFile = File(...),
):
    temp_path = os.path.join(BASE_DIR, f"temp_{template_file.filename}")

    with open(temp_path, "wb") as f:
        f.write(await template_file.read())

    try:
        if template_file.filename.endswith(".docx"):
            template = extract_docx(temp_path)
        elif template_file.filename.endswith(".pdf"):
            template = extract_pdf(temp_path)
        else:
            os.remove(temp_path)
            return {"error": "Format non supporté"}

        os.remove(temp_path)

        subprocess.run([
            "py",
            os.path.join(BASE_DIR, "scrappers", "generate_letter.py"),
            job_description,
            company_description,
            template,
        ], cwd=BASE_DIR)

        letter_path = os.path.join(BASE_DIR, "generated_letter.json")
        if os.path.exists(letter_path):
            with open(letter_path, "r", encoding="utf-8") as f:
                return json.load(f)

        return {"error": "lettre non générée"}

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {"error": str(e)}