from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from scrapers.indeed import scrape_indeed
from scrapers.hellowork import scrape_hellowork
from scrapers.wtj import scrape_wtj
from scrapers.jobteaser import scrape_jobteaser
from scrapers.monster import scrape_monster
from scrapers.francetravail import scrape_francetravail
from utils.database import save_jobs, clear_jobs

app = Flask(__name__)

def filter_scam_schools(jobs):
    scam_keywords = [
        "ecole", "école", "campus", "formation", "cfa", "institut", 
        "mydigitalschool", "openclassrooms", "epitech", "epsi", "cesi", 
        "sup de vinci", "esgi", "guardia", "ironhack", "doranco", "eni", 
        "wild code school", "o'clock", "simplon", "m2i", "aston", "euridis",
        "isitech", "ipssi", "supinfo", "etna", "web@cademie", "groupe alternance"
    ]
    filtered = []
    for job in jobs:
        c_lower = job.get("company", "").lower()
        if not any(kw in c_lower for kw in scam_keywords):
            filtered.append(job)
    return filtered


def get_jobs():
    conn = sqlite3.connect("data/jobs.db")
    c = conn.cursor()

    c.execute("SELECT title, company, link, source, location, job_type FROM jobs ORDER BY id DESC")
    jobs = c.fetchall()

    conn.close()
    return jobs

@app.route("/")
def index():
    jobs = get_jobs()
    return render_template("index.html", jobs=jobs)

@app.route("/search", methods=["POST"])
def search():
    keyword = request.form.get("keyword", "cyber")
    location = request.form.get("location", "France")
    job_type = request.form.get("job_type", "")
    
    # On combine le type de contrat au mot-clé (ex: "Alternance Developpeur Web")
    full_keyword = f"{job_type} {keyword}".strip()
    
    # Nettoyer les anciens résultats
    clear_jobs()
    
    jobs = []
    try:
        jobs += scrape_indeed(full_keyword, location, job_type)
    except Exception as e:
        print("Erreur globale Indeed:", e)
        
    try:
        jobs += scrape_hellowork(full_keyword, location, job_type)
    except Exception as e:
        print("Erreur globale Hellowork:", e)
        
    try:
        jobs += scrape_wtj(full_keyword, location, job_type)
    except Exception as e:
        print("Erreur globale WTJ:", e)
        
    try:
        jobs += scrape_jobteaser(full_keyword, location, job_type)
    except Exception as e:
        print("Erreur globale Jobteaser:", e)
        
    try:
        jobs += scrape_monster(full_keyword, location, job_type)
    except Exception as e:
        print("Erreur globale Monster:", e)
        
    try:
        jobs += scrape_francetravail(full_keyword, location, job_type)
    except Exception as e:
        print("Erreur globale France Travail:", e)
    
    # Filtrer les fausses offres des écoles/scams
    jobs = filter_scam_schools(jobs)
    
    if jobs:
        save_jobs(jobs)
        
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)