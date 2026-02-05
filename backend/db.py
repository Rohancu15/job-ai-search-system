import sqlite3
from datetime import datetime

DB_PATH = "backend/applied_jobs.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS applied_jobs (
            job_id INTEGER PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            skills TEXT,
            experience TEXT,
            description TEXT,
            applied_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def apply_job(job: dict):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO applied_jobs 
        (job_id, title, company, location, skills, experience, description, applied_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job["job_id"],
        job["title"],
        job["company"],
        job["location"],
        job["skills"],
        job["experience"],
        job["description"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def get_applied_jobs():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT * FROM applied_jobs ORDER BY applied_at DESC")
    rows = cur.fetchall()

    conn.close()

    results = []
    for r in rows:
        results.append({
            "job_id": r[0],
            "title": r[1],
            "company": r[2],
            "location": r[3],
            "skills": r[4],
            "experience": r[5],
            "description": r[6],
            "applied_at": r[7],
        })

    return results


def delete_applied_job(job_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DELETE FROM applied_jobs WHERE job_id=?", (job_id,))
    conn.commit()
    conn.close()
