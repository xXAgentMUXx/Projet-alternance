import os
import sqlite3


def ensure_db_dir(db_path="data/jobs.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)


def init_db(db_path="data/jobs.db"):
    ensure_db_dir(db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        link TEXT UNIQUE,
        source TEXT,
        location TEXT,
        job_type TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_jobs(jobs, db_path="data/jobs.db"):
    ensure_db_dir(db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for job in jobs:
        try:
            c.execute("""
            INSERT INTO jobs (title, company, link, source, location, job_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (job.get("title"), job.get("company"), job.get("link"), job.get("source"), job.get("location", "Non précisé"), job.get("job_type", "Non précisé")))
        except Exception:
            pass  # évite doublons ou erreurs

    conn.commit()
    conn.close()


def clear_jobs(db_path="data/jobs.db"):
    ensure_db_dir(db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM jobs")
    conn.commit()
    conn.close()
