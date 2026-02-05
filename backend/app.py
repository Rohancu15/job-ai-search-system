from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import pandas as pd
import requests
import msgpack
import json
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer

from backend.db import init_db, apply_job, get_applied_jobs, delete_applied_job

# ==========================
# CONFIG
# ==========================
CSV_PATH = "data/jobs.csv"
ENDEE_URL = "http://localhost:8080"
INDEX_NAME = "jobs_index"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"

app = FastAPI(title="Job AI Search API", version="2.0.0")

# ==========================
# ✅ Lazy Globals
# ==========================
df = None
model = None

# ✅ Init DB once
init_db()


def load_resources():
    """Loads CSV + embedding model only when needed"""
    global df, model

    if df is None:
        df = pd.read_csv(CSV_PATH)

        # ✅ Normalize important filter columns
        df["location"] = df["location"].astype(str).str.strip().str.title()
        df["experience"] = df["experience"].astype(str).str.strip()

    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")


# ==========================
# HOME
# ==========================
@app.get("/")
def home():
    return {"message": "✅ Job AI API running"}


# ==========================
# INSERT JOBS INTO ENDEE
# ==========================
@app.post("/insert")
def insert_jobs():
    load_resources()

    payload = []

    for _, row in df.iterrows():
        text = f"{row['title']} {row['skills']} {row['description']}"
        embedding = model.encode(text).tolist()

        location = str(row["location"]).strip().title()
        experience = str(row["experience"]).strip()

        payload.append(
            {
                "id": str(row["job_id"]),
                "vector": embedding,
                "meta": {
                    "title": str(row["title"]),
                    "company": str(row["company"]),
                    "location": location,
                    "skills": str(row["skills"]),
                    "experience": experience,
                    "description": str(row["description"]),
                },
                # ✅ Endee expects filter as JSON STRING
                "filter": json.dumps(
                    {
                        "location": location,
                        "experience": experience,
                    }
                ),
            }
        )

    try:
        res = requests.post(
            f"{ENDEE_URL}/api/v1/index/{INDEX_NAME}/vector/insert",
            json=payload,
            timeout=30,  # ✅ prevents infinite LOADING
        )
    except Exception as e:
        return {"error": f"Endee insert failed: {str(e)}"}

    return {
        "status_code": res.status_code,
        "response": res.text,
        "inserted": len(payload),
    }


# ==========================
# SEARCH JOBS
# ==========================
class SearchRequest(BaseModel):
    query: str
    location: str | None = None
    experience: str | None = None
    k: int = 5


@app.post("/search")
def search_jobs(req: SearchRequest):
    load_resources()

    query_text = req.query.strip()

    # ✅ ignore swagger default "string"
    if query_text.lower() == "string" or len(query_text) == 0:
        return []

    query_vector = model.encode(query_text).tolist()

    filter_array = []

    if req.location and req.location.strip().lower() not in ["", "string", "all"]:
        loc = req.location.strip().title()
        filter_array.append({"location": {"$eq": loc}})

    if req.experience and req.experience.strip().lower() not in ["", "string", "all"]:
        exp = req.experience.strip()
        filter_array.append({"experience": {"$eq": exp}})

    # ✅ Important: use BIGGER K if filters are ON
    # because Endee first retrieves by vector then applies filter.
    endee_k = max(int(req.k), 50) if len(filter_array) > 0 else int(req.k)

    payload = {"vector": query_vector, "k": endee_k}

    if len(filter_array) > 0:
        payload["filter"] = json.dumps(filter_array)

    try:
        res = requests.post(
            f"{ENDEE_URL}/api/v1/index/{INDEX_NAME}/search",
            json=payload,
            timeout=15,
        )
    except Exception as e:
        return {"error": f"Endee search failed: {str(e)}"}

    if res.status_code != 200:
        return {"error": res.text}

    data = msgpack.unpackb(res.content, raw=False)

    results = []
    for item in data:
        # ✅ Endee may return: [score, id] OR [score, id, meta/filter...]
        score = float(item[0])
        job_id = int(item[1])

        job = df[df["job_id"] == job_id]
        if job.empty:
            continue

        job = job.iloc[0]

        results.append(
            {
                "job_id": int(job["job_id"]),
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "skills": job["skills"],
                "experience": job["experience"],
                "description": job["description"],
                "score": score,
            }
        )

    # ✅ return only top req.k (after filter)
    return results[: int(req.k)]


# ==========================
# APPLY JOB
# ==========================
class ApplyRequest(BaseModel):
    job_id: int


@app.post("/apply")
def apply_jobs(req: ApplyRequest):
    load_resources()

    job = df[df["job_id"] == req.job_id]
    if job.empty:
        return {"error": "Job not found"}

    job_data = job.iloc[0].to_dict()
    job_data["job_id"] = int(job_data["job_id"])

    apply_job(job_data)
    return {"message": f"✅ Applied to job_id {req.job_id}"}


@app.get("/applied")
def applied_jobs():
    return get_applied_jobs()


@app.delete("/applied/{job_id}")
def remove_applied(job_id: int):
    delete_applied_job(job_id)
    return {"message": f"✅ Removed job_id {job_id} from applied list"}


# ==========================
# RESUME MATCHING (PDF)
# ==========================
@app.post("/resume-match")
async def resume_match(file: UploadFile = File(...), k: int = 5):
    load_resources()

    if not file.filename.lower().endswith(".pdf"):
        return {"error": "Only PDF resumes are supported"}

    pdf_bytes = await file.read()

    # ✅ Extract resume text
    resume_text = ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        resume_text += page.get_text()

    resume_text = resume_text.strip()

    if len(resume_text) < 30:
        return {"error": "Resume text is too short / unreadable PDF"}

    resume_vector = model.encode(resume_text).tolist()

    payload = {
        "vector": resume_vector,
        "k": int(k),
    }

    try:
        res = requests.post(
            f"{ENDEE_URL}/api/v1/index/{INDEX_NAME}/search",
            json=payload,
            timeout=15,
        )
    except Exception as e:
        return {"error": f"Endee resume-match failed: {str(e)}"}

    if res.status_code != 200:
        return {"error": res.text}

    data = msgpack.unpackb(res.content, raw=False)

    results = []
    for item in data:
        score = float(item[0])
        job_id = int(item[1])

        job = df[df["job_id"] == job_id]
        if job.empty:
            continue

        job = job.iloc[0]

        results.append(
            {
                "job_id": int(job["job_id"]),
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "skills": job["skills"],
                "experience": job["experience"],
                "description": job["description"],
                "score": score,
            }
        )

    return results[: int(k)]


# ==========================
# ✅ RAG WITH OLLAMA (NO OPENAI KEY)
# ==========================
class RagRequest(BaseModel):
    question: str
    k: int = 5


@app.post("/rag")
def rag_answer(req: RagRequest):
    load_resources()

    question = req.question.strip()
    if len(question) == 0:
        return {"answer": "Please enter a question.", "context_jobs": []}

    # ✅ Retrieve relevant jobs from Endee
    q_vec = model.encode(question).tolist()

    payload = {"vector": q_vec, "k": max(int(req.k), 10)}

    try:
        res = requests.post(
            f"{ENDEE_URL}/api/v1/index/{INDEX_NAME}/search",
            json=payload,
            timeout=15,
        )
    except Exception as e:
        return {"error": f"Endee RAG search failed: {str(e)}"}

    if res.status_code != 200:
        return {"error": res.text}

    data = msgpack.unpackb(res.content, raw=False)

    context_jobs = []
    for item in data[: int(req.k)]:
        score = float(item[0])
        job_id = int(item[1])

        job = df[df["job_id"] == job_id]
        if job.empty:
            continue

        job = job.iloc[0]

        context_jobs.append(
            {
                "job_id": int(job["job_id"]),
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "skills": job["skills"],
                "experience": job["experience"],
                "description": job["description"],
                "score": score,
            }
        )

    if not context_jobs:
        return {"answer": "No jobs found for your query.", "context_jobs": []}

    # ✅ Build prompt for Ollama
    context_text = ""
    for j in context_jobs:
        context_text += f"""
Job ID: {j['job_id']}
Title: {j['title']}
Company: {j['company']}
Location: {j['location']}
Experience: {j['experience']}
Skills: {j['skills']}
Description: {j['description']}
Score: {j['score']}
---
"""

    prompt = f"""
You are a helpful Job Recommendation AI assistant.
Use ONLY the below job context to answer the user question.
If user asks something not possible from context, say "Not enough data in jobs context".

USER QUESTION:
{question}

JOBS CONTEXT:
{context_text}

Give a helpful answer and mention best matching job titles.
"""

    # ✅ Call Ollama locally
    try:
        ollama_res = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=60,
        )
    except Exception as e:
        return {"error": f"Ollama call failed: {str(e)}", "context_jobs": context_jobs}

    if ollama_res.status_code != 200:
        return {"error": ollama_res.text, "context_jobs": context_jobs}

    answer = ollama_res.json().get("response", "No response generated.")

    return {"answer": answer, "context_jobs": context_jobs}
