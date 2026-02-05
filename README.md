# 🚀 Job AI Search System

An end-to-end **AI-powered Job Search & Recommendation System** that allows users to search jobs using semantic search, apply to jobs, track applied jobs, match resumes, and ask questions using RAG (Retrieval Augmented Generation).

---

## ✨ Features

- 🔍 **Semantic Job Search** (title / skills based)
- 📍 Filter by **Location** and **Experience**
- 📄 **Resume Matching** using embeddings
- 🧠 **RAG Assistant** (Ask questions about jobs)
- ❤️ Apply jobs & track **Applied Jobs**
- ⚡ Fast vector search using **Endee Vector DB**
- 🖥️ Interactive UI built with **Streamlit**
- 🧩 Backend API built using **FastAPI**

---

## 🧱 Tech Stack

| Layer | Technology |
|-----|-----------|
Frontend | Streamlit  
Backend | FastAPI  
Vector DB | Endee  
Embeddings | Sentence-Transformers (MiniLM)  
Database | SQLite  
RAG LLM | Ollama (LLaMA)  
Language | Python  

---
## 📂 Project Structure
job-ai-project/
│
├── backend/
│ ├── app.py
│ ├── db.py
│ └── applied_jobs.db
│
├── frontend/
│ └── streamlit_app.py
│
├── data/
│ └── jobs.csv
│
├── scripts/
│ ├── create_index.py
│ ├── insert_jobs.py
│ └── search_jobs.py
│
└── README.md


---

## 🧠 System Architecture

┌────────────┐
│ Streamlit │
│ Frontend │
└─────┬──────┘
│ REST API
┌─────▼──────┐
│ FastAPI │
│ Backend │
└─────┬──────┘
│
┌────▼─────┐ ┌──────────────┐
│ Endee DB │◄───►│ Embeddings │
└──────────┘ │ MiniLM Model │
└──────────────┘
│
┌────▼─────┐
│ SQLite │
│ Applied │
│ Jobs DB │
└──────────┘


---

## ▶️ How to Run the Project

### 1️⃣ Start Endee Vector DB
```bash
docker run -p 8080:8080 endeedb/endee

2️⃣ Create Vector Index
python scripts/create_index.py

3️⃣ Insert Jobs into Vector DB
python scripts/insert_jobs.py

4️⃣ Start Backend API
python -m uvicorn backend.app:app --reload

API runs at:
http://localhost:8000

5️⃣ Start Frontend (Streamlit)
streamlit run frontend/streamlit_app.py
UI runs at:
http://localhost:8501



