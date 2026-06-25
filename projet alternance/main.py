from unittest import result

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
import re
import hashlib
import urllib.request
import urllib.error
import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone
from scrappers.smart_recruiter import get_jobs as get_smartrecruiters_jobs
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.responses import StreamingResponse
import asyncio

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
    greenhouse_boards: list[str] | None = None
    lever_boards: list[str] | None = None
    wttj_slugs: list[str] | None = None
    smartrecruiters_companies: list[str] | None = None


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
    "apec":             os.path.join(BASE_DIR, "apec_jobs.json"),
    "hellowork":        os.path.join(BASE_DIR, "hellowork_jobs.json"),
    "francetravail":    os.path.join(BASE_DIR, "francetravail_jobs.json"),
    "greenhouse": os.path.join(BASE_DIR, "greenhouse_jobs.json"),
    "lever": os.path.join(BASE_DIR, "lever_jobs.json"),
    "wttj": os.path.join(BASE_DIR, "wttj_jobs.json"),
    "smartrecruiters": os.path.join(BASE_DIR, "smartrecruiters_jobs.json"),
}

SEEN_JOBS_FILE = os.path.join(BASE_DIR, "seen_jobs.json")
AUTO_NOTIFICATION_FILE = os.path.join(BASE_DIR, "auto_notifications.json")
NOTIFICATION_CONFIG_FILE = os.path.join(BASE_DIR, "notification_config.json")
WTTJ_SLUGS_FILE = os.path.join(BASE_DIR, "wttj_slugs.json")
BOARDS_CONFIG_FILE = os.path.join(BASE_DIR, "boards_config.json")
SMARTRECRUITERS_CONFIG_FILE = os.path.join(BASE_DIR, "smartrecruiters_config.json")

scheduler = None

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
    "greenhouse": "Greenhouse",
    "lever": "Lever",
    "smartrecruiters": "SmartRecruiters",
}

GREENHOUSE_BOARDS = []
LEVER_BOARDS = []
SMARTRECRUITERS_COMPANIES = []
SMARTRECRUITERS_MAX_JOBS_PER_COMPANY = 200

auto_search_running = False


def city_to_department_code(city: str) -> str | None:
    if not city:
        return None

    normalized = city.strip().lower()
    normalized = normalized.replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a").replace("ç", "c").replace("î", "i").replace("ô", "o").replace("ù", "u")
    normalized = normalized.replace("'", "")

    if normalized.isdigit():
        return normalized

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

    for start in [text.rfind("["), text.rfind("{")]:
        if start == -1:
            continue
        candidate = text[start:]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

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

    lines.append(
        f"🚀 {payload.get('total_new_jobs', 0)} nouvelles offres détectées"
    )

    for source, stats in payload.get("source_results", {}).items():

        jobs = stats.get("jobs", [])

        if not jobs:
            continue

        lines.append("")
        lines.append(f"📌 {source} ({len(jobs)} nouvelles)")

        for job in jobs:

            title = job.get("title", "Offre")
            company = job.get("company", "")
            location = job.get("location", "")
            url = job.get("url", "")

            lines.append(
                f"• {title} | {company} | {location}"
            )

            if url:
                lines.append(url)

    return "\n".join(lines)


DISCORD_MAX_LENGTH = 1900  


def split_discord_message(content: str, limit=DISCORD_MAX_LENGTH):
    chunks = []
    current = ""

    for line in content.split("\n"):
        if len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            continue

        if len(current) + len(line) + 1 > limit:
            chunks.append(current)
            current = line
        else:
            current += ("\n" if current else "") + line

    if current:
        chunks.append(current)

    return chunks


def send_discord_webhook(webhook_url: str, payload: dict | str) -> bool:
    try:
        if isinstance(payload, str):
            content = payload
        else:
            content = build_notification_content(payload)

        chunks = split_discord_message(content)

        print(f"Discord : {len(chunks)} messages à envoyer")

        for i, chunk in enumerate(chunks, 1):

            body = json.dumps(
                {
                    "content": chunk
                },
                ensure_ascii=False
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
                print(
                    f"Discord message {i}/{len(chunks)} envoyé :",
                    response.getcode()
                )

        return True

    except urllib.error.HTTPError as e:
        print(f"[!] Erreur webhook Discord : {e.code} {e.reason}")

        try:
            print(
                "[!] Corps Discord :",
                e.read().decode("utf-8", errors="ignore")
            )
        except:
            pass

    except Exception as e:
        print("[!] Erreur Discord :", e)

    return False

def send_email_notification(email_to: str, payload: dict | str) -> bool:
    cfg = load_notification_config()
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = cfg.get("gmailUser") or os.environ.get("EMAIL_SMTP_USERNAME")
    smtp_pass = cfg.get("gmailAppPassword") or os.environ.get("EMAIL_SMTP_PASSWORD")
    email_from = smtp_user

    if not smtp_user or not smtp_pass:
        print("[!] Gmail non configuré : renseigne l'adresse Gmail et le mot de passe d'application dans l'interface.")
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

def sanitize_board_urls(urls, prefix):
    return [
        url.strip()
        for url in (urls or [])
        if isinstance(url, str) and url.strip().startswith(prefix)
    ]


def sanitize_smartrecruiters_companies(companies):
    valid = []
    for value in companies or []:
        if not isinstance(value, str):
            continue

        company = value.strip()
        match = re.search(r"smartrecruiters\.com/([^/?#]+)", company, re.IGNORECASE)
        if match:
            company = match.group(1)

        if re.match(r"^[A-Za-z0-9][A-Za-z0-9_-]*$", company):
            valid.append(company)

    return list(dict.fromkeys(valid))


def text_matches_query(text: str, query: str) -> bool:
    tokens = [
        token
        for token in re.split(r"\s+", (query or "").strip().lower())
        if token
    ]
    if not tokens:
        return True
    text = (text or "").lower()
    return all(token in text for token in tokens)


def text_matches_any_query_token(text: str, query: str) -> bool:
    tokens = [
        token
        for token in re.split(r"\s+", (query or "").strip().lower())
        if len(token) >= 3
    ]
    if not tokens:
        return True
    text = (text or "").lower()
    return any(token in text for token in tokens)


def smartrecruiters_posting_search_text(posting: dict, company_slug: str) -> str:
    location = posting.get("location") or {}
    if not isinstance(location, dict):
        location = {"city": str(location)}

    company = posting.get("company") or {}
    if isinstance(company, dict):
        company = company.get("name", "")

    parts = [
        posting.get("name", ""),
        company or company_slug,
        location.get("city", ""),
        location.get("region", ""),
        location.get("country", ""),
        posting.get("releasedDate", ""),
    ]
    return " ".join(str(part) for part in parts if part).lower()


def normalize_smartrecruiters_job(job: dict, details: dict | None, company_slug: str) -> dict:
    details = details or {}
    location = details.get("location") or job.get("location") or {}
    if not isinstance(location, dict):
        location = {"city": str(location)}

    location_parts = [
        location.get("city"),
        location.get("region"),
        location.get("country"),
    ]

    company = details.get("company") or job.get("company") or {}
    if isinstance(company, dict):
        company_name = company.get("name") or company_slug
    else:
        company_name = company or company_slug

    sections = details.get("jobAd", {}).get("sections", {}) if isinstance(details.get("jobAd"), dict) else {}
    description = (
        sections.get("jobDescription")
        or details.get("description")
        or job.get("description")
        or ""
    )
    posting_id = details.get("id") or job.get("id") or job.get("uuid")
    fallback_url = f"https://jobs.smartrecruiters.com/{company_slug}/{posting_id}" if posting_id else ""

    return {
        "title": details.get("name") or job.get("name") or "",
        "company": company_name,
        "location": ", ".join(part for part in location_parts if part),
        "url": details.get("postingUrl") or job.get("postingUrl") or details.get("applyUrl") or job.get("ref") or fallback_url,
        "description": description,
        "source": "SmartRecruiters",
        "type": "offre",
        "contract": [],
        "remote": "",
        "created_at": details.get("releasedDate") or job.get("releasedDate") or "",
    }


def run_scraper(script_name, keyword, city, board_urls=None):
    try:
        if script_name == "linkedin":
            script_path = os.path.join(
                BASE_DIR, "scrappers", "JobSpy-main", "linkedin_jobs.py"
            )
            json_file = JSON_FILES[script_name]

            result = subprocess.run(
                ["python", script_path],
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
                ["python", script_path],
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
                ["python", script_path, keyword, city or "", department_code],
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
            marked = mark_new_jobs(jobs, script_name)
            with open(JSON_FILES["apec"], "w", encoding="utf-8") as f:
                json.dump(marked, f, ensure_ascii=False, indent=2)
            return marked

        elif script_name in ("hellowork", "francetravail"):
            script_path = os.path.join(
                BASE_DIR, "scrappers", "job-scraper-main", "main.py"
            )

            result = subprocess.run(
                [
                    "python",
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
            marked = mark_new_jobs(jobs, script_name)
            with open(JSON_FILES[script_name], "w", encoding="utf-8") as f:
                json.dump(
                    marked,
                    f,
                    ensure_ascii=False,
                    indent=2
                )
            return marked
        elif script_name == "greenhouse":
            all_jobs = []
            boards = sanitize_board_urls(board_urls, "https://boards.greenhouse.io/") or GREENHOUSE_BOARDS
            for board_url in boards:
                script_path = os.path.join(BASE_DIR, "scrappers", "greenhouse.io-scraper-main", "main.py")
                result = subprocess.run(
                    ["python", script_path, keyword, board_url],
                    capture_output=True, text=True, cwd=BASE_DIR,
                )
                if result.stderr:
                    print("[stderr greenhouse]", result.stderr[:300])
                data = parse_json_stdout(result.stdout)
                if isinstance(data, list):
                    all_jobs.extend(data)
            if not all_jobs:
                return []
            marked = mark_new_jobs(all_jobs, "greenhouse")
            with open(JSON_FILES["greenhouse"], "w", encoding="utf-8") as f:
                json.dump(marked, f, ensure_ascii=False, indent=2)
            return marked

        elif script_name == "lever":
            all_jobs = []
            boards = sanitize_board_urls(board_urls, "https://jobs.lever.co/") or LEVER_BOARDS
            for board_url in boards:
                script_path = os.path.join(BASE_DIR, "scrappers", "greenhouse.io-scraper-main", "lever.py")
                result = subprocess.run(
                    ["python", script_path, keyword, board_url],
                    capture_output=True, text=True, cwd=BASE_DIR,
                )
                if result.stderr:
                    print("[stderr lever]", result.stderr[:300])
                data = parse_json_stdout(result.stdout)
                if isinstance(data, list):
                    all_jobs.extend(data)
            if not all_jobs:
                return []
            marked = mark_new_jobs(all_jobs, "lever")
            with open(JSON_FILES[script_name], "w", encoding="utf-8") as f:
                json.dump(marked, f, ensure_ascii=False, indent=2)
            return marked
        elif script_name == "smartrecruiters":
            all_jobs = []
            companies = sanitize_smartrecruiters_companies(board_urls) or SMARTRECRUITERS_COMPANIES

            for company_slug in companies:
                try:
                    
                    postings = get_smartrecruiters_jobs(
                        company_slug,
                        keyword=keyword,
                        city=city,
                        max_jobs=SMARTRECRUITERS_MAX_JOBS_PER_COMPANY,
                    )

                    print(
                        f"[SMART] {company_slug}: "
                        f"{len(postings)} offres récupérées"
                    )

                    for p in postings[:5]:
                        print(
                            "[SMART TITLE]",
                            p.get("name")
                        )

                    all_jobs.extend(
                        normalize_smartrecruiters_job(
                            p,
                            None,
                            company_slug
                        )
                        for p in postings
                    )

                except Exception as e:
                    print(
                        f"[stderr smartrecruiters] "
                        f"{company_slug}: {e}"
                    )

                keyword_matches = []
                fallback_jobs = []

                for posting in postings:
                    posting_searchable = smartrecruiters_posting_search_text(posting, company_slug)
                    job = normalize_smartrecruiters_job(posting, None, company_slug)
                    fallback_jobs.append(job)

                    if not text_matches_any_query_token(posting_searchable, keyword):
                        continue

                    keyword_matches.append(job)
                    if not city or text_matches_any_query_token(posting_searchable, city):
                        all_jobs.append(job)

                if not all_jobs and keyword_matches:
                    all_jobs.extend(keyword_matches[:50])
                elif not all_jobs:
                    all_jobs.extend(fallback_jobs[:50])

            if not all_jobs:
                return []
            marked = mark_new_jobs(all_jobs, "smartrecruiters")
            with open(JSON_FILES["smartrecruiters"], "w", encoding="utf-8") as f:
                json.dump(marked, f, ensure_ascii=False, indent=2)
            return marked
        elif script_name == "wttj":
            slugs_arg = []
            if os.path.exists(WTTJ_SLUGS_FILE):
                try:
                    with open(WTTJ_SLUGS_FILE, "r", encoding="utf-8") as f:
                        slugs_arg = json.load(f)
                except Exception:
                    slugs_arg = []
            script_path = os.path.join(BASE_DIR, "scrappers", "wttj.py")
            cmd = ["python", script_path, keyword]
            if slugs_arg:
                cmd.append(WTTJ_SLUGS_FILE)
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE_DIR)
            if result.stderr:
                print("[stderr wttj]", result.stderr)
            data = parse_json_stdout(result.stdout)
            if not isinstance(data, list):
                return []
            marked = mark_new_jobs(data, "wttj")
            with open(JSON_FILES["wttj"], "w", encoding="utf-8") as f:
                json.dump(marked, f, ensure_ascii=False, indent=2)
            return marked
        else:
            script_path = os.path.join(
                BASE_DIR, "scrappers", f"{script_name}.py"
            )
            json_file = JSON_FILES[script_name]

            result = subprocess.run(
                ["python", script_path],
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
    gmailUser: str | None = None
    gmailAppPassword: str | None = None


@app.get("/notification-config")
def notification_config():
    config = load_notification_config()
    return {
        "discordWebhook": config.get("discordWebhook", ""),
        "email": config.get("email", ""),
        "sendDiscord": config.get("sendDiscord", False),
        "sendEmail": config.get("sendEmail", False),
        "gmailUser": config.get("gmailUser", ""),
        "gmailAppPassword": config.get("gmailAppPassword", ""),

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
            "error": "Recherche automatique en cours ou imminente"
        }

    scrapers = {
        "LinkedIn": ("linkedin", data.greenhouse_boards),
        "Indeed": ("indeed", None),
        "Meteojob": ("meteojob", None),
        "Bonne Alternance": ("bonne_alternance", None),
        "APEC": ("apec", None),
        "HelloWork": ("hellowork", None),
        "France Travail": ("francetravail", None),
        "Greenhouse": ("greenhouse", data.greenhouse_boards),
        "Lever": ("lever", data.lever_boards),
        "WTTJ": ("wttj", None),
        "SmartRecruiters": ("smartrecruiters", data.smartrecruiters_companies),
    }

    results = {}

    def run(name, args):
        script, boards = args
        return name, run_scraper(script, data.keyword, data.city, boards)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(run, name, args)
            for name, args in scrapers.items()
        ]

        for future in as_completed(futures):
            name, jobs = future.result()
            results[name] = jobs

    return results


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

@app.post("/search/Greenhouse")
def search_greenhouse(data: SearchRequest):
    if not can_manual_search():
        return {"jobs": [], "error": "Recherche automatique en cours."}
    if not sanitize_board_urls(data.greenhouse_boards, "https://boards.greenhouse.io/") and not GREENHOUSE_BOARDS:
        return {"jobs": [], "error": "Aucun board Greenhouse configure."}
    return {"jobs": run_scraper("greenhouse", data.keyword, data.city, data.greenhouse_boards)}


@app.post("/search/Lever")
def search_lever(data: SearchRequest):
    if not can_manual_search():
        return {"jobs": [], "error": "Recherche automatique en cours."}
    if not sanitize_board_urls(data.lever_boards, "https://jobs.lever.co/") and not LEVER_BOARDS:
        return {"jobs": [], "error": "Aucun board Lever configure."}
    return {"jobs": run_scraper("lever", data.keyword, data.city, data.lever_boards)}


@app.post("/search/SmartRecruiters")
def search_smartrecruiters(data: SearchRequest):
    if not can_manual_search():
        return {"jobs": [], "error": "Recherche automatique en cours."}
    if not sanitize_smartrecruiters_companies(data.smartrecruiters_companies) and not SMARTRECRUITERS_COMPANIES:
        return {"jobs": [], "error": "Aucune entreprise SmartRecruiters configuree."}
    return {
        "jobs": run_scraper(
            "smartrecruiters",
            data.keyword,
            data.city,
            data.smartrecruiters_companies,
        )
    }


class BoardsConfigRequest(BaseModel):
    greenhouse_boards: list[str] = []
    lever_boards: list[str] = []


class SmartRecruitersConfigRequest(BaseModel):
    companies: list[str] = []


@app.get("/boards-config")
def get_boards_config():
    return {"greenhouse_boards": GREENHOUSE_BOARDS, "lever_boards": LEVER_BOARDS}


@app.post("/boards-config")
def set_boards_config(data: BoardsConfigRequest):
    import re as _re
    global GREENHOUSE_BOARDS, LEVER_BOARDS
    GREENHOUSE_BOARDS = [u for u in data.greenhouse_boards if _re.match(r"https://boards\.greenhouse\.io/", u)]
    LEVER_BOARDS      = [u for u in data.lever_boards      if _re.match(r"https://jobs\.lever\.co/",       u)]
    with open(BOARDS_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "greenhouse_boards": GREENHOUSE_BOARDS,
                "lever_boards": LEVER_BOARDS,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    return {"greenhouse_boards": GREENHOUSE_BOARDS, "lever_boards": LEVER_BOARDS}


@app.get("/smartrecruiters-config")
def get_smartrecruiters_config():
    return {"companies": SMARTRECRUITERS_COMPANIES}


@app.post("/smartrecruiters-config")
def set_smartrecruiters_config(data: SmartRecruitersConfigRequest):
    global SMARTRECRUITERS_COMPANIES
    SMARTRECRUITERS_COMPANIES = sanitize_smartrecruiters_companies(
        data.companies
    )
    with open(
        SMARTRECRUITERS_CONFIG_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            {"companies": SMARTRECRUITERS_COMPANIES},
            f,
            ensure_ascii=False,
            indent=2
        )
    return {"companies": SMARTRECRUITERS_COMPANIES}


@app.post("/search/WTTJ")
@app.post("/search/Welcome to the Jungle")
def search_wttj(data: SearchRequest):
    if not can_manual_search():
        return {"jobs": [], "error": "Recherche automatique en cours."}
    return {"jobs": run_scraper("wttj", data.keyword, data.city)}


class WttjSlugsRequest(BaseModel):
    slugs: list[str] = []


@app.get("/wttj-slugs")
def get_wttj_slugs():
    """Retourne la liste des slugs WTTJ configurés."""
    if os.path.exists(WTTJ_SLUGS_FILE):
        try:
            with open(WTTJ_SLUGS_FILE, "r", encoding="utf-8") as f:
                return {"slugs": json.load(f)}
        except Exception:
            pass
    return {"slugs": []}


@app.post("/wttj-slugs")
def set_wttj_slugs(data: WttjSlugsRequest):
    """Sauvegarde la liste des slugs WTTJ à scraper."""
    import re as _re
    valid = [
        s.strip().lower()
        for s in data.slugs
        if isinstance(s, str) and re.match(r'^[a-z0-9][a-z0-9\-]*$', s.strip().lower())
    ]
    try:
        with open(WTTJ_SLUGS_FILE, "w", encoding="utf-8") as f:
            json.dump(valid, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return {"error": str(e)}
    return {"slugs": valid}


@app.get("/wttj-companies")
def get_wttj_companies():
    """Retourne la liste des entreprises WTTJ disponibles (depuis le cache)."""
    companies_file = os.path.join(BASE_DIR, "wttj_companies.json")
    if not os.path.exists(companies_file):
        return {"companies": [], "message": "Cache non disponible, lancez une première recherche."}
    try:
        with open(companies_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        companies = [
            {
                "slug":  c.get("path", "")[14:],
                "name":  c.get("name", ""),
            }
            for c in data.get("companies", [])
            if c.get("path")
        ]
        return {"companies": companies}
    except Exception as e:
        return {"error": str(e), "companies": []}


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
            "python",
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


class CompanyContactRequest(BaseModel):
    company: str


@app.post("/company-contacts")
def company_contacts(data: CompanyContactRequest):
    try:

        result = subprocess.run(
            [
                "python",
                os.path.join(
                    BASE_DIR,
                    "scrappers",
                    "company_contact_finder.py"
                ),
                data.company,
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
        )

        if result.returncode != 0:
            return {
                "error": result.stderr
            }
        print("STDOUT =")
        print(result.stdout)

        contacts = json.loads(result.stdout)

        return contacts

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
            "python",
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

    print("\n===================================")
    print("Recherche automatique démarrée")
    print("===================================")

    scrapers = [
        "linkedin",
        "indeed",
        "meteojob",
        "bonne_alternance",
        "apec",
        "hellowork",
        "francetravail",
        "greenhouse",
        "lever",
        "wttj",
        "smartrecruiters",
    ]

    auto_summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_results": {},
        "total_jobs": 0,
        "total_new_jobs": 0,
    }

    def run_one(scraper: str):
        try:
            print(f"[AUTO] Recherche sur {scraper}...")

            if scraper == "greenhouse":
                if not GREENHOUSE_BOARDS:
                    return scraper, []
                jobs = run_scraper(scraper, keyword, city, GREENHOUSE_BOARDS)

            elif scraper == "lever":
                if not LEVER_BOARDS:
                    return scraper, []
                jobs = run_scraper(scraper, keyword, city, LEVER_BOARDS)

            elif scraper == "smartrecruiters":
                if not SMARTRECRUITERS_COMPANIES:
                    return scraper, []
                jobs = run_scraper(scraper, keyword, city, SMARTRECRUITERS_COMPANIES)

            else:
                jobs = run_scraper(scraper, keyword, city)

            return scraper, jobs

        except Exception as e:
            return scraper, {"error": str(e)}

    try:
        with ThreadPoolExecutor(max_workers=6) as executor:

            futures = [
                executor.submit(run_one, scraper)
                for scraper in scrapers
            ]

            for future in as_completed(futures):
                scraper, jobs = future.result()

                if not isinstance(jobs, list):
                    auto_summary["source_results"][scraper] = {
                        "total_jobs": 0,
                        "new_jobs": 0,
                        "error": True,
                    }
                    continue

                new_jobs = [j for j in jobs if j.get("is_new")]

                auto_summary["source_results"][scraper] = {
                    "total_jobs": len(jobs),
                    "new_jobs": len(new_jobs),
                    "jobs": [
                        {
                            "title": j.get("title"),
                            "company": j.get("company"),
                            "location": j.get("location"),
                            "url": j.get("url"),
                        }
                        for j in new_jobs[:5]
                    ]
                }

                auto_summary["total_jobs"] += len(jobs)
                auto_summary["total_new_jobs"] += len(new_jobs)

                print(
                    f"[AUTO] {scraper}: "
                    f"{len(jobs)} jobs ({len(new_jobs)} new)"
                )

    finally:
        save_auto_notification(auto_summary)

        config = load_notification_config()

        if auto_summary["total_new_jobs"] > 0:

            if config.get("sendDiscord") and config.get("discordWebhook"):
                send_discord_webhook(config["discordWebhook"], auto_summary)

            if config.get("sendEmail") and config.get("email"):
                send_email_notification(config["email"], auto_summary)

        else:
            print("Aucune nouvelle offre")

        auto_search_running = False

        print("===================================")
        print("Recherche automatique terminée")
        print("===================================\n")


@app.get("/auto-results")
def get_auto_results():
    """Retourne les résultats de la dernière recherche automatique (tous scrapers)."""
    platform_map = {
        "LinkedIn":          "linkedin",
        "Indeed":            "indeed",
        "Meteojob":          "meteojob",
        "Bonne Alternance":  "bonne_alternance",
        "APEC":              "apec",
        "HelloWork":         "hellowork",
        "France Travail":    "francetravail",
        "Greenhouse":        "greenhouse",
        "Lever":             "lever",
        "WTTJ":              "wttj",
        "Welcome to the Jungle": "wttj",
        "SmartRecruiters":   "smartrecruiters",
    }

    all_jobs = {}
    for display_name, key in platform_map.items():
        json_path = JSON_FILES.get(key)
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if key == "bonne_alternance" and isinstance(raw, dict):
                    raw = normalize_lba(raw)
                    raw = mark_new_jobs(raw, key)
                all_jobs[display_name] = raw if isinstance(raw, list) else []
            except Exception as e:
                print(f"[!] Erreur lecture {key}: {e}")
                all_jobs[display_name] = []
        else:
            all_jobs[display_name] = []

    return all_jobs


@app.on_event("startup")
def start_scheduler():

    global scheduler
    global GREENHOUSE_BOARDS
    global LEVER_BOARDS
    global SMARTRECRUITERS_COMPANIES

    if scheduler is not None:
        return

    print("Chargement des configurations...")

    if os.path.exists(BOARDS_CONFIG_FILE):

        try:

            with open(
                BOARDS_CONFIG_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                cfg = json.load(f)

            GREENHOUSE_BOARDS = cfg.get(
                "greenhouse_boards",
                []
            )

            LEVER_BOARDS = cfg.get(
                "lever_boards",
                []
            )

            print(
                f"Greenhouse chargés : {len(GREENHOUSE_BOARDS)}"
            )

            print(
                f"Lever chargés : {len(LEVER_BOARDS)}"
            )

        except Exception as e:

            print(
                f"Erreur chargement boards : {e}"
            )


    smart_file = os.path.join(
        BASE_DIR,
        "smartrecruiters_config.json"
    )

    if os.path.exists(smart_file):

        try:

            with open(
                smart_file,
                "r",
                encoding="utf-8"
            ) as f:

                cfg = json.load(f)

            SMARTRECRUITERS_COMPANIES = cfg.get(
                "companies",
                []
            )

            print(
                f"SmartRecruiters chargés : "
                f"{len(SMARTRECRUITERS_COMPANIES)}"
            )

        except Exception as e:

            print(
                f"Erreur SmartRecruiters : {e}"
            )

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
