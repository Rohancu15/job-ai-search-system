import requests

ENDEE_URL = "http://localhost:8080"
INDEX_NAME = "jobs_index"

payload = {
    "index_name": INDEX_NAME,
    "dim": 384,
    "space_type": "cosine"
}

res = requests.post(f"{ENDEE_URL}/api/v1/index/create", json=payload)

print("Status:", res.status_code)
print("Response:", res.text)
