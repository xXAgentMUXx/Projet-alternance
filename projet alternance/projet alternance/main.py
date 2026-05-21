from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from docx import Document
from PyPDF2 import PdfReader
import subprocess
import json
import os


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


def extract_docx(path):
    doc = Document(path)
    text = []

    for p in doc.paragraphs:
        if p.text.strip():
            text.append(p.text)

    return "\n".join(text)


def extract_pdf(path):
    reader = PdfReader(path)
    text = ""

    for page in reader.pages:
        txt = page.extract_text()
        if txt:
            text += txt + "\n"

    return text


def run_scraper(script_name, keyword, city):
    try:

        if script_name == "linkedin":
            script_path = os.path.join(
                "scrappers",
                "JobSpy-main",
                "linkedin_jobs.py"
            )
            json_file = "linkedin_jobs.json"

        elif script_name == "indeed":
            script_path = os.path.join(
                "scrappers",
                "JobSpy-main",
                "indeed_jobs.py"
            )
            json_file = "indeed_jobs.json"

        else:
            script_path = os.path.join(
                "scrappers",
                f"{script_name}.py"
            )
            json_file = f"{script_name}_jobs.json"

        result = subprocess.run(
            ["py", script_path],
            input=f"{keyword}\n{city}",
            text=True,
            capture_output=True
        )

        print(result.stdout)
        print(result.stderr)

        if os.path.exists(json_file):
            with open(
                json_file,
                "r",
                encoding="utf-8"
            ) as f:
                return json.load(f)

        return []

    except Exception as e:
        return {
            "error": str(e)
        }


@app.post("/search-all")
def search_all(data: SearchRequest):
    return {
        "LinkedIn": run_scraper(
            "linkedin",
            data.keyword,
            data.city
        ),
        "Indeed": run_scraper(
            "indeed",
            data.keyword,
            data.city
        ),
        "Meteojob": run_scraper(
            "meteojob",
            data.keyword,
            data.city
        ),
        "Bonne Alternance": run_scraper(
            "bonne_alternance",
            data.keyword,
            data.city
        )
    }


@app.post("/search/LinkedIn")
def search_linkedin(data: SearchRequest):
    return {
        "jobs": run_scraper(
            "linkedin",
            data.keyword,
            data.city
        )
    }


@app.post("/search/Indeed")
def search_indeed(data: SearchRequest):
    return {
        "jobs": run_scraper(
            "indeed",
            data.keyword,
            data.city
        )
    }


@app.post("/search/Meteojob")
def search_meteojob(data: SearchRequest):
    return {
        "jobs": run_scraper(
            "meteojob",
            data.keyword,
            data.city
        )
    }


@app.post("/search/Bonne Alternance")
def search_bonne_alternance(data: SearchRequest):
    return {
        "jobs": run_scraper(
            "bonne_alternance",
            data.keyword,
            data.city
        )
    }

@app.post("/generate-letter")
async def generate_letter(
    job_description: str = Form(...),
    company_description: str = Form(...),
    template_file: UploadFile = File(...)
):

    temp_path = f"temp_{template_file.filename}"

    with open(temp_path, "wb") as f:
        f.write(await template_file.read())

    try:

        if template_file.filename.endswith(".docx"):
            template = extract_docx(temp_path)

        elif template_file.filename.endswith(".pdf"):
            template = extract_pdf(temp_path)

        else:
            os.remove(temp_path)
            return {
                "error": "Format non supporté"
            }

        os.remove(temp_path)

        subprocess.run(
            [
                "py",
                "scrappers/generate_letter.py",
                job_description,
                company_description,
                template
            ]
        )

        if os.path.exists("generated_letter.json"):
            with open(
                "generated_letter.json",
                "r",
                encoding="utf-8"
            ) as f:
                return json.load(f)

        return {
            "error": "lettre non générée"
        }

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return {
            "error": str(e)
        }