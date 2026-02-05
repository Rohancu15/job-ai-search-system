import pandas as pd
import requests
import json
from sentence_transformers import SentenceTransformer

CSV_PATH = "data/jobs.csv"
ENDEE_URL = "http://localhost:8080"
INDEX_NAME = "jobs_index"

df = pd.read_csv(CSV_PATH)
model = SentenceTransformer("all-MiniLM-L6-v2")

payload = []

for _, row in df.iterrows():
    text = f"{row['title']} {row['skills']} {row['description']}"
    embedding = model.encode(text).tolist()

    payload.append({
        "id": str(row["job_id"]),
        "vector": embedding,
        "meta": {
            "title": str(row["title"]),
            "company": str(row["company"]),
            "location": str(row["location"]),
            "skills": str(row["skills"]),
            "experience": str(row["experience"]),
            "description": str(row["description"])
        },

        # ✅ filter must be STRING JSON
        "filter": json.dumps({
            "location": str(row["location"]).strip().lower(),
            "experience": str(row["experience"]).strip().lower()
        })
    })

res = requests.post(
    f"{ENDEE_URL}/api/v1/index/{INDEX_NAME}/vector/insert",
    json=payload
)

print("Status:", res.status_code)
print("Response:", res.text)
print("Inserted vectors:", len(payload))
