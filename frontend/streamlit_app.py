import streamlit as st
import pandas as pd
import requests

API_URL = "http://127.0.0.1:8000"
CSV_PATH = "data/jobs.csv"

st.set_page_config(page_title="Job AI Search System", layout="wide")

st.title("💼 Job AI Search System")
st.caption("Semantic Search + Filters + Apply Jobs + Resume Match + RAG (Endee + Ollama) ✅")

# Load CSV for dropdown options
df = pd.read_csv(CSV_PATH)
df["location"] = df["location"].astype(str).str.strip().str.title()
df["experience"] = df["experience"].astype(str).str.strip()

locations = ["All"] + sorted(df["location"].unique().tolist())
experiences = ["All"] + sorted(df["experience"].unique().tolist())

queries = [
    "python backend developer",
    "aws cloud engineer",
    "data analyst",
    "devops engineer",
    "machine learning engineer",
    "java developer",
]

# Sidebar
st.sidebar.header("🔍 Filters")
selected_location = st.sidebar.selectbox("Location", locations)
selected_experience = st.sidebar.selectbox("Experience", experiences)
k = st.sidebar.slider("Top K Results", 1, 10, 5)

st.sidebar.header("⚙ Admin Panel")
if st.sidebar.button("📥 Insert Jobs to Endee"):
    r = requests.post(f"{API_URL}/insert")
    if r.status_code == 200:
        st.sidebar.success("✅ Jobs inserted into Endee!")
    else:
        st.sidebar.error(r.text)

# Tabs
tab1, tab2, tab3 = st.tabs(["🔎 Search Jobs", "📄 Resume Match", "🧠 RAG Assistant"])

# ---------------- TAB 1 SEARCH ----------------
with tab1:
    st.subheader("🔎 Search Jobs")
    query = st.selectbox("Select Job Query", queries)

    if st.button("🔍 Search Jobs"):
        payload = {"query": query, "k": k}

        if selected_location != "All":
            payload["location"] = selected_location

        if selected_experience != "All":
            payload["experience"] = selected_experience

        res = requests.post(f"{API_URL}/search", json=payload)

        if res.status_code != 200:
            st.error(res.text)
        else:
            jobs = res.json()

            if not jobs:
                st.warning("No jobs found 😕")
            else:
                st.success(f"✅ Found {len(jobs)} jobs")

                for job in jobs:
                    st.markdown(f"### {job['title']} ⭐ {job['score']:.3f}")
                    st.write(f"🏢 {job['company']} | 📍 {job['location']} | 🧑‍💻 {job['experience']}")
                    st.write(f"🛠 Skills: {job['skills']}")
                    st.write(job["description"])

                    if st.button(f"✅ Apply Job {job['job_id']}", key=f"apply_{job['job_id']}"):
                        apply_res = requests.post(f"{API_URL}/apply", json={"job_id": job["job_id"]})
                        if apply_res.status_code == 200:
                            st.success(apply_res.json()["message"])
                            st.rerun()
                        else:
                            st.error(apply_res.text)

                    st.markdown("---")

# ---------------- TAB 2 RESUME MATCH ----------------
with tab2:
    st.subheader("📄 Resume Upload Job Matching (PDF Only)")
    resume_file = st.file_uploader("Upload Resume PDF", type=["pdf"])
    resume_k = st.slider("Top Resume Matches", 1, 10, 5)

    if st.button("📌 Match Resume to Jobs"):
        if resume_file is None:
            st.warning("Upload a PDF resume first.")
        else:
            files = {"file": (resume_file.name, resume_file.getvalue(), "application/pdf")}
            res = requests.post(f"{API_URL}/resume-match?k={resume_k}", files=files)

            if res.status_code != 200:
                st.error(res.text)
            else:
                matches = res.json()
                if isinstance(matches, dict) and "error" in matches:
                    st.error(matches["error"])
                elif not matches:
                    st.warning("No matching jobs found.")
                else:
                    st.success(f"✅ Found {len(matches)} resume matches")
                    for job in matches:
                        st.markdown(f"### {job['title']} ⭐ {job['score']:.3f}")
                        st.write(f"🏢 {job['company']} | 📍 {job['location']} | 🧑‍💻 {job['experience']}")
                        st.write(f"🛠 Skills: {job['skills']}")
                        st.write(job["description"])
                        st.markdown("---")

# ---------------- TAB 3 RAG ----------------
with tab3:
    st.subheader("🧠 RAG Assistant (Endee + Ollama llama3.2)")
    question = st.text_area("Ask your question (RAG):", "Which job is best for me if I know Python and FastAPI?")
    rag_k = st.slider("Top Jobs Context (RAG)", 1, 10, 5)

    if st.button("✨ Generate AI Answer (RAG)"):
        payload = {"question": question, "k": rag_k}
        res = requests.post(f"{API_URL}/rag", json=payload)

        if res.status_code != 200:
            st.error(res.text)
        else:
            out = res.json()
            st.success("✅ AI Answer Generated")
            st.markdown("### ✅ AI Answer")
            st.write(out.get("answer", ""))

            st.markdown("### 📌 Retrieved Jobs (Context)")
            ctx = out.get("context", [])
            if not ctx:
                st.warning("No context jobs retrieved.")
            else:
                for j in ctx:
                    st.markdown(f"- **{j['title']}** ({j['company']}) | {j['location']} | {j['experience']} | ⭐ {j['score']:.3f}")

# ---------------- APPLIED JOBS SECTION ----------------
st.divider()
st.subheader("📌 Applied Jobs")

try:
    applied_res = requests.get(f"{API_URL}/applied")

    if applied_res.status_code == 200:
        applied_jobs = applied_res.json()

        if not applied_jobs:
            st.info("No applied jobs yet.")
        else:
            st.success(f"✅ You applied to {len(applied_jobs)} jobs")

            for aj in applied_jobs:
                st.markdown(f"✅ **{aj['title']}** ({aj['company']}) - {aj['location']} - {aj['experience']}")
                st.caption(f"Applied at: {aj['applied_at']}")

                if st.button(f"❌ Remove {aj['job_id']}", key=f"remove_{aj['job_id']}"):
                    del_res = requests.delete(f"{API_URL}/applied/{aj['job_id']}")
                    if del_res.status_code == 200:
                        st.success("Removed ✅ Refreshing...")
                        st.rerun()
                    else:
                        st.error(del_res.text)

                st.markdown("---")
    else:
        st.error(applied_res.text)

except Exception as e:
    st.error(f"Backend not running: {e}")

