import os
import sqlite3


DEFAULT_DATABASE = "data/jobs.db"

def prepare_directory(database_path):
    folder = os.path.dirname(database_path)
    os.makedirs(folder, exist_ok=True)


def open_connection(database_path):
    prepare_directory(database_path)
    return sqlite3.connect(database_path)


def init_db(database_path=DEFAULT_DATABASE):

    with open_connection(database_path) as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                company TEXT,
                link TEXT UNIQUE,
                source TEXT,
                location TEXT,
                job_type TEXT
            )
            """
        )

        connection.commit()


def save_jobs(jobs, database_path=DEFAULT_DATABASE):

    query = """
        INSERT INTO jobs
        (
            title,
            company,
            link,
            source,
            location,
            job_type
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """

    with open_connection(database_path) as connection:

        cursor = connection.cursor()

        for offer in jobs:

            values = (
                offer.get("title"),
                offer.get("company"),
                offer.get("link"),
                offer.get("source"),
                offer.get("location", "Non précisé"),
                offer.get("job_type", "Non précisé"),
            )

            try:
                cursor.execute(query, values)
            except sqlite3.IntegrityError:
                continue
            except sqlite3.Error:
                continue

        connection.commit()


def clear_jobs(database_path=DEFAULT_DATABASE):

    with open_connection(database_path) as connection:

        connection.execute("DELETE FROM jobs")
        connection.commit()