from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from staffspy import LinkedInAccount
from docx import Document
from pypdf import PdfReader
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import json
import os
import hashlib
import urllib.request
import urllib.error
import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone


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


class FollowupRequest(BaseModel):
    person: dict | None = None
    company: str | None = None
    job_description: str | None = None
    company_description: str | None = None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

JSON_FILES = {
    "linkedin":         os.path.join(BASE_DIR, "linkedin_jobs.json"),
    "indeed":           os.path.join(BASE_DIR, "indeed_jobs.json"),
    "meteojob":         os.path.join(BASE_DIR, "meteojob_jobs.json"),
    "bonne_alternance": os.path.join(BASE_DIR, "lba_montpellier_dev.json"),
}

SEEN_JOBS_FILE = os.path.join(BASE_DIR, "seen_jobs.json")
AUTO_NOTIFICATION_FILE = os.path.join(BASE_DIR, "auto_notifications.json")
NOTIFICATION_CONFIG_FILE = os.path.join(BASE_DIR, "notification_config.json")

DEPARTMENT_MAP = {
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
    "saint etienne": "42",
    "perpignan": "66",
    "toulon": "83",
    "aubagne": "13",
    "calais": "62",
    "le havre": "76",
    "le mans": "72",
    "amiens": "80",
    "metz": "57",
    "nancy": "54",
    "caen": "14",
    "bayonne": "64",
    "montauban": "82",
    "brest": "29",
}

PLATFORM_DISPLAY_NAMES = {
    "hellowork": "HelloWork",
    "francetravail": "France Travail",
    "apec": "APEC",
    "linkedin": "LinkedIn",
    "indeed": "Indeed",
    "bonne_alternance": "Bonne Alternance",
    "meteojob": "Meteojob",
}

auto_search_running = False


def city_to_department_code(city: str) -> str | None:
    if not city:
        return None

    normalized = city.strip().lower()
    normalized = normalized.replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a").replace("ç", "c").replace("î", "i").replace("ô", "o").replace("ù", "u")
    normalized = normalized.replace("'", "")

    if normalized.isdigit():
        return normalized

    # If the city string contains a department code like "Montpellier 34" or "Montpellier (34)"
    import re
    match = re.search(r"\b(\d{2,3})\b", normalized)
    if match:
        return match.group(1)

    return DEPARTMENT_MAP.get(normalized)


def parse_json_stdout(stdout: str):
    text = stdout.strip()
    if not text:
        return None

    import re

    # Prefer the last JSON-like object/array in the output, because logs may contain '[' or '{'.
    for start in [text.rfind("["), text.rfind("{")]:
        if start == -1:
            continue
        candidate = text[start:]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    # Fallback to parsing the last line if the CLI prints JSON there.
    last_line = text.splitlines()[-1]
    try:
        return json.loads(last_line)
    except Exception:
        return None


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

    display_name = PLATFORM_DISPLAY_NAMES.get(platform, platform)
    for job in jobs:
        if not job.get("url") and job.get("link"):
            job["url"] = job.get("link")

        fp = job_fingerprint(job)
        if fp not in seen:
            seen[fp] = platform
            job["is_new"] = True
            updated = True
        else:
            job["is_new"] = False

        job["source"] = display_name
        result.append(job)

    if updated:
        save_seen_jobs(seen)

    return result

def save_auto_notification(summary: dict):
    try:
        with open(AUTO_NOTIFICATION_FILE, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[!] Impossible de sauvegarder l'état des notifications automatiques : {e}")


def load_auto_notification() -> dict:
    if not os.path.exists(AUTO_NOTIFICATION_FILE):
        return {}
    try:
        with open(AUTO_NOTIFICATION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_notification_config(config: dict):
    try:
        with open(NOTIFICATION_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[!] Impossible de sauvegarder la configuration de notification : {e}")


def load_notification_config() -> dict:
    if not os.path.exists(NOTIFICATION_CONFIG_FILE):
        return {}
    try:
        with open(NOTIFICATION_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def build_notification_content(payload: dict) -> str:
    lines = []

    if payload.get("message"):
        lines.append(payload["message"])
    else:
        lines.append("Notification de suivi de candidature")

    if payload.get("total_new_jobs", 0) > 0:
        lines.append(f"Nouvelles offres détectées : {payload['total_new_jobs']}.")
    else:
        lines.append("Aucune nouvelle offre détectée.")

    for source, stats in payload.get("source_results", {}).items():
        if stats.get("new_jobs", 0) > 0:
            lines.append(f"- {source} : {stats['new_jobs']} nouvelles")

    follow_ups = payload.get("follow_up_notifications", []) or []
    if follow_ups:
        lines.append("\nRelances à préparer :")
        for alert in follow_ups:
            if alert.get("type") == "overdue":
                lines.append(f"- {alert.get('company')} : en retard de {alert.get('days')} jour(s)")
            elif alert.get("type") == "due_soon":
                lines.append(f"- {alert.get('company')} : dans {alert.get('days')} jour(s)")

    missing = payload.get("pending_relance_companies", []) or []
    if missing:
        lines.append("\nCandidatures sans contact de relance :")
        for company in missing:
            lines.append(f"- {company}")

    return "\n".join(lines)


def send_discord_webhook(webhook_url: str, payload: dict | str) -> bool:
    print(type(webhook_url))
    print(len(webhook_url))
    try:
        if isinstance(payload, str):
            content = payload
        else:
            content = build_notification_content(payload)

        print("Webhook utilisé :", repr(webhook_url))
        print("Message envoyé :", content)
        body = json.dumps(
            {
                "content": content
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            webhook_url.strip(),
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:

            print("Status :", response.getcode())
            response_body = response.read().decode(
                "utf-8",
                errors="ignore"
            )
            print("Réponse Discord :", response_body)
            return 200 <= response.getcode() < 300

    except urllib.error.HTTPError as e:
        print(
            f"[!] Erreur webhook Discord : "
            f"{e.code} {e.reason}"
        )
        try:
            error_body = e.read().decode(
                "utf-8",
                errors="ignore"
            )
            print(
                "[!] Corps de la réponse Discord :",
                error_body
            )
        except Exception:
            pass
    except Exception as e:
        print(
            f"[!] Erreur webhook Discord : {e}"
        )
    return False

def send_email_notification(email_to: str, payload: dict | str) -> bool:
    smtp_host = os.environ.get("EMAIL_SMTP_HOST")
    smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
    smtp_user = os.environ.get("EMAIL_SMTP_USERNAME")
    smtp_pass = os.environ.get("EMAIL_SMTP_PASSWORD")
    email_from = os.environ.get("EMAIL_FROM") or smtp_user

    if not smtp_host or not smtp_user or not smtp_pass or not email_from:
        print("[!] SMTP non configuré : définissez EMAIL_SMTP_HOST, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD et EMAIL_FROM")
        return False

    if isinstance(payload, str):
        body_content = payload
    else:
        body_content = build_notification_content(payload)

    subject = "Notification alternance"
    if isinstance(payload, dict) and payload.get("total_new_jobs", 0) > 0:
        subject = "Nouvelles offres alternance disponibles"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = email_from
    message["To"] = email_to
    message.set_content(body_content)

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(message)
        server.quit()
        return True
    except Exception as e:
        print(f"[!] Erreur envoi email : {e}")
        return False


def get_scheduler_status():
    job = scheduler.get_job("scheduled_search_job") if "scheduler" in globals() else None
    next_run = job.next_run_time if job else None
    if next_run is not None and next_run.tzinfo is None:
        next_run = next_run.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    countdown = None
    if next_run is not None:
        countdown = int(max(0, (next_run.astimezone(timezone.utc) - now).total_seconds()))

    manual_enabled = not auto_search_running and (countdown is None or countdown > 0)

    return {
        "next_run_time": next_run.isoformat() if next_run is not None else None,
        "countdown": countdown,
        "auto_running": auto_search_running,
        "manual_enabled": manual_enabled,
    }


def can_manual_search():
    status = get_scheduler_status()
    return status["manual_enabled"]

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


def _build_followup_message(person: dict | None, company: str | None, job_description: str | None, company_description: str | None) -> str:
    name = (person or {}).get("name") if person else None
    recipient = name or (company or "recruteur")

    job_part = "le poste" if not job_description else f"le poste de {job_description}"
    company_part = company or (person or {}).get("current_company") or "votre entreprise"

    intro = f"Bonjour {recipient},\n\n"
    body = (
        f"Je me permets de revenir vers vous concernant ma candidature pour {job_part} chez {company_part}. "
        "Je reste très motivé par cette opportunité et je souhaitais savoir si vous aviez eu le temps d'examiner mon dossier."
    )

    details = "\n\nVous trouverez en pièce jointe mon CV et ma lettre de motivation."
    closing = "\n\nJe suis disponible pour échanger à votre convenance.\n\nBien cordialement,\n"
    sender = (person or {}).get("name") or "[Votre nom]"

    return intro + body + details + closing + sender


@app.post("/generate-followup")
def generate_followup(data: FollowupRequest):
    try:
        msg = _build_followup_message(
            person=data.person,
            company=data.company,
            job_description=data.job_description,
            company_description=data.company_description,
        )

        return {"message": msg}
    except Exception as e:
        return {"error": str(e)}

def run_scraper(script_name, keyword, city):
    try:
        if script_name == "linkedin":
            script_path = os.path.join(
                BASE_DIR, "scrappers", "JobSpy-main", "linkedin_jobs.py"
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

            jobs = data
            return mark_new_jobs(jobs, script_name)

        elif script_name == "indeed":
            script_path = os.path.join(
                BASE_DIR, "scrappers", "JobSpy-main", "indeed_jobs.py"
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

            jobs = data
            return mark_new_jobs(jobs, script_name)

        elif script_name == "apec":
            department_code = city_to_department_code(city)
            if not department_code:
                print(f"[!] APEC scraper nécessite un code de département pour la ville '{city}'")
                return []

            script_path = os.path.join(
                BASE_DIR, "scrappers", "scraping-jobs-master", "index.py"
            )

            result = subprocess.run(
                ["py", script_path, keyword, city or "", department_code],
                capture_output=True,
                text=True,
                cwd=BASE_DIR,
            )

            stdout = result.stdout.strip()
            if result.stderr:
                print("[stderr]", result.stderr[:500])

            if not stdout:
                print("[!] APEC scraper n'a pas retourné de données")
                return []

            data = parse_json_stdout(stdout)
            if data is None:
                print("[!] Impossible de parser la sortie APEC")
                return []

            jobs = normalize_apec(data)
            return mark_new_jobs(jobs, script_name)

        elif script_name in ("hellowork", "francetravail"):
            script_path = os.path.join(
                BASE_DIR, "scrappers", "job-scraper-main", "main.py"
            )

            result = subprocess.run(
                [
                    "py",
                    script_path,
                    "--keyword",
                    keyword,
                    "--location",
                    city or "France",
                    "--sources",
                    script_name,
                    "--print-json",
                ],
                capture_output=True,
                text=True,
                cwd=BASE_DIR,
            )

            stdout = result.stdout.strip()
            if result.stderr:
                print("[stderr]", result.stderr[:500])

            if not stdout:
                print(f"[!] {script_name} scraper n'a pas retourné de données")
                return []

            data = parse_json_stdout(stdout)
            if data is None:
                print(f"[!] Impossible de parser la sortie {script_name} : {stdout[:500]}" )
                return []

            jobs = data
            return mark_new_jobs(jobs, script_name)

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

            if script_name == "bonne_alternance":
                jobs = normalize_lba(data)
            else:
                jobs = data

            return mark_new_jobs(jobs, script_name)

    except Exception as e:
        print(f"[!] Erreur run_scraper({script_name}) : {e}")
        return {"error": str(e)}

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


def normalize_apec(data: list) -> list:
    result = []
    for job in data:
        result.append({
            "title":       job.get("title", ""),
            "company":     job.get("company", ""),
            "location":    job.get("location", ""),
            "url":         job.get("link", ""),
            "phone":       "",
            "description": job.get("description", ""),
            "source":      "APEC",
            "type":        "offre",
            "contract":    [],
            "remote":      "",
            "created_at":  job.get("publication_date", ""),
        })

    return result

@app.get("/scheduler-status")
def scheduler_status():
    return get_scheduler_status()


@app.get("/notifications")
def notifications():
    summary = load_auto_notification()
    if not summary:
        return {
            "total_new_jobs": 0,
            "source_results": {},
            "timestamp": None,
        }
    return summary


class NotificationConfigRequest(BaseModel):
    discordWebhook: str | None = None
    email: str | None = None
    sendDiscord: bool = False
    sendEmail: bool = False


@app.get("/notification-config")
def notification_config():
    config = load_notification_config()
    return {
        "discordWebhook": config.get("discordWebhook", ""),
        "email": config.get("email", ""),
        "sendDiscord": config.get("sendDiscord", False),
        "sendEmail": config.get("sendEmail", False),
    }


class NotificationDispatchRequest(BaseModel):
    message: str | None = None
    total_new_jobs: int = 0
    source_results: dict = {}
    follow_up_notifications: list[dict] = []
    pending_relance_companies: list[str] = []


@app.post("/notification-config")
def save_notification_config_route(data: NotificationConfigRequest):
    config = {
        "discordWebhook": data.discordWebhook or "",
        "email": data.email or "",
        "sendDiscord": data.sendDiscord,
        "sendEmail": data.sendEmail,
    }
    save_notification_config(config)
    return {"saved": True}


@app.post("/notify")
def notify(data: NotificationDispatchRequest):
    config = load_notification_config()
    if not config.get("sendDiscord") and not config.get("sendEmail"):
        return {"error": "Aucun canal de notification configuré."}

    payload = {
        "message": data.message,
        "total_new_jobs": data.total_new_jobs,
        "source_results": data.source_results,
        "follow_up_notifications": data.follow_up_notifications,
        "pending_relance_companies": data.pending_relance_companies,
    }

    results = {
        "sentDiscord": False,
        "sentEmail": False,
        "errors": [],
    }

    if config.get("sendDiscord") and config.get("discordWebhook"):
        results["sentDiscord"] = send_discord_webhook(config["discordWebhook"], payload)
        if not results["sentDiscord"]:
            results["errors"].append("Discord non envoyé")

    if config.get("sendEmail") and config.get("email"):
        results["sentEmail"] = send_email_notification(config["email"], payload)
        if not results["sentEmail"]:
            results["errors"].append("Email non envoyé")

    return results


@app.post("/search-all")
def search_all(data: SearchRequest):
    if not can_manual_search():
        return {
            "jobs": [],
            "error": "Recherche automatique en cours ou imminente, recherche manuelle désactivée."
        }

    return {
        "LinkedIn":         run_scraper("linkedin",         data.keyword, data.city),
        "Indeed":           run_scraper("indeed",           data.keyword, data.city),
        "Meteojob":         run_scraper("meteojob",         data.keyword, data.city),
        "Bonne Alternance": run_scraper("bonne_alternance", data.keyword, data.city),
        "APEC":             run_scraper("apec",             data.keyword, data.city),
        "HelloWork":        run_scraper("hellowork",        data.keyword, data.city),
        "France Travail":   run_scraper("francetravail",   data.keyword, data.city),
    }


@app.post("/search/LinkedIn")
def search_linkedin(data: SearchRequest):
    return {"jobs": run_scraper("linkedin", data.keyword, data.city)}


@app.post("/search/Indeed")
def search_indeed(data: SearchRequest):
    if not can_manual_search():
        return {"jobs": [], "error": "Recherche automatique en cours ou imminente, recherche manuelle désactivée."}
    return {"jobs": run_scraper("indeed", data.keyword, data.city)}


@app.post("/search/Meteojob")
def search_meteojob(data: SearchRequest):
    if not can_manual_search():
        return {"jobs": [], "error": "Recherche automatique en cours ou imminente, recherche manuelle désactivée."}
    return {"jobs": run_scraper("meteojob", data.keyword, data.city)}


@app.post("/search/Bonne Alternance")
def search_bonne_alternance(data: SearchRequest):
    if not can_manual_search():
        return {"jobs": [], "error": "Recherche automatique en cours ou imminente, recherche manuelle désactivée."}
    return {"jobs": run_scraper("bonne_alternance", data.keyword, data.city)}


@app.post("/search/APEC")
def search_apec(data: SearchRequest):
    if not can_manual_search():
        return {"jobs": [], "error": "Recherche automatique en cours ou imminente, recherche manuelle désactivée."}
    return {"jobs": run_scraper("apec", data.keyword, data.city)}


@app.post("/search/HelloWork")
def search_hellowork(data: SearchRequest):
    if not can_manual_search():
        return {"jobs": [], "error": "Recherche automatique en cours ou imminente, recherche manuelle désactivée."}
    return {"jobs": run_scraper("hellowork", data.keyword, data.city)}


@app.post("/search/France Travail")
def search_france_travail(data: SearchRequest):
    if not can_manual_search():
        return {"jobs": [], "error": "Recherche automatique en cours ou imminente, recherche manuelle désactivée."}
    return {"jobs": run_scraper("francetravail", data.keyword, data.city)}


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
    

class StaffSpyRequest(BaseModel):
    company: str
    location: str = ""
    role: str = ""
    max_results: int = 20


@app.post("/search-company-contacts")
def search_company_contacts(data: StaffSpyRequest):

    try:
        account = LinkedInAccount(
            session_file="session.pkl",
            log_level=1
        )

        staff = account.scrape_staff(
            company_name=data.company,
            search_term=data.role,
            location=data.location,
            max_results=data.max_results
        )

        staff = staff.where(staff.notna(), None)

        return {
            "people": staff.to_dict(orient="records")
        }

    except Exception as e:
        return {
            "error": str(e)
        }
    
class MessageRequest(BaseModel):
    contact_name: str
    company_name: str
    headline: str = ""
    company_description: str
    job_description: str
    motivation_letter: str = ""


@app.post("/generate-message")
def generate_message(data: MessageRequest):

    try:

        subprocess.run([
            "py",
            os.path.join(
                BASE_DIR,
                "scrappers",
                "create_message.py"
            ),
            json.dumps({
                "contact_name": data.contact_name,
                "company_name": data.company_name,
                "headline": data.headline,
                "company_description": data.company_description,
                "job_description": data.job_description,
                "motivation_letter": data.motivation_letter
            }, ensure_ascii=False)
        ])

        with open(
            os.path.join(
                BASE_DIR,
                "generated_message.json"
            ),
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception as e:
        return {"error": str(e)}
    

def scheduled_search():
    global auto_search_running

    keyword = "alternance développeur"
    city = "Montpellier"

    auto_search_running = True
    print("===================================")
    print("Recherche automatique démarrée")
    print("===================================")

    scrapers = [
        "linkedin",
        "indeed",
        "meteojob",
        "bonne_alternance",
        "apec",
        "hellowork",
        "francetravail"
    ]

    auto_summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_results": {},
        "total_jobs": 0,
        "total_new_jobs": 0,
    }

    try:
        for scraper in scrapers:
            try:
                print(f"Recherche sur {scraper}...")

                jobs = run_scraper(
                    scraper,
                    keyword,
                    city
                )

                if isinstance(jobs, list):
                    new_jobs = [
                        job for job in jobs
                        if job.get("is_new")
                    ]

                    auto_summary["source_results"][scraper] = {
                        "total_jobs": len(jobs),
                        "new_jobs": len(new_jobs),
                    }
                    auto_summary["total_jobs"] += len(jobs)
                    auto_summary["total_new_jobs"] += len(new_jobs)

                    print(
                        f"{scraper}: "
                        f"{len(jobs)} offres "
                        f"({len(new_jobs)} nouvelles)"
                    )
                else:
                    auto_summary["source_results"][scraper] = {
                        "total_jobs": 0,
                        "new_jobs": 0,
                        "error": True,
                    }
                    print(
                        f"{scraper}: erreur"
                    )

            except Exception as e:
                auto_summary["source_results"][scraper] = {
                    "total_jobs": 0,
                    "new_jobs": 0,
                    "error": True,
                    "message": str(e),
                }
                print(
                    f"Erreur {scraper}: {e}"
                )
    finally:
        save_auto_notification(auto_summary)

        config = load_notification_config()
        if auto_summary.get("total_new_jobs", 0) > 0:
            if config.get("sendDiscord") and config.get("discordWebhook"):
                sent = send_discord_webhook(config.get("discordWebhook"), auto_summary)
                print(f"Webhook Discord envoyé: {sent}")

            if config.get("sendEmail") and config.get("email"):
                sent = send_email_notification(config.get("email"), auto_summary)
                print(f"Email envoyé: {sent}")
        else:
            print("Aucune nouvelle offre, notifications non envoyées.")

        auto_search_running = False
        print("===================================")
        print("Recherche automatique terminée")
        print("===================================")

scheduler = None

@app.on_event("startup")
def start_scheduler():
    global scheduler
    if scheduler is not None:
        return

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        scheduled_search,
        trigger="interval",
        hours=3,
        max_instances=1,
        id="scheduled_search_job"
    )
    scheduler.start()
    print("Scheduler démarré")
    scheduled_search()

@app.on_event("shutdown")
def stop_scheduler():
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None

