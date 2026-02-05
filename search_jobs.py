import pandas as pd
import requests
import msgpack
import json
from sentence_transformers import SentenceTransformer

CSV_PATH = "data/jobs.csv"
ENDEE_URL = "http://localhost:8080"
INDEX_NAME = "jobs_index"

df = pd.read_csv(CSV_PATH)

# ✅ Normalize CSV (important)
df["location"] = df["location"].astype(str).str.strip().str.lower()
df["experience"] = df["experience"].astype(str).str.strip()

query = input("Enter job query: ").strip()
location = input("Enter location (or leave empty): ").strip()
experience = input("Enter experience (or leave empty): ").strip()

model = SentenceTransformer("all-MiniLM-L6-v2")
query_vector = model.encode(query).tolist()

payload = {
    "vector": query_vector,
    "k": 50  # ✅ keep 10 for better filter chance
}

res = requests.post(f"{ENDEE_URL}/api/v1/index/{INDEX_NAME}/search", json=payload)

print("\nStatus:", res.status_code)

if res.status_code != 200:
    print("Error:", res.text)
    exit()

data = msgpack.unpackb(res.content, raw=False)

print("\n✅ Raw Results from Endee:", len(data))

# ✅ Manual Filtering in Python (100% Reliable)
filtered = []

for item in data:
    score = float(item[0])
    job_id = int(item[1])

    job = df[df["job_id"] == job_id].iloc[0]

    ok = True

    if location:
        if job["location"] != location.strip().lower():
            ok = False

    if experience:
        if job["experience"] != experience.strip():
            ok = False

    if ok:
        filtered.append((score, job_id))

print("\n✅ Top Matching Jobs (After Filtering):\n")

if not filtered:
    print("No jobs found 😕 (filter not matching)")
    exit()

for score, job_id in filtered:
    job = df[df["job_id"] == job_id].iloc[0]

    print(f"⭐ Score: {score:.3f}")
    print(f"   Job ID: {job_id}")
    print(f"   Title: {job['title']}")
    print(f"   Company: {job['company']}")
    print(f"   Location: {job['location'].title()}")
    print(f"   Skills: {job['skills']}")
    print(f"   Experience: {job['experience']}")
    print("-" * 50)
