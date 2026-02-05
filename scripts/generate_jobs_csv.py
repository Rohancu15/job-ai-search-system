import pandas as pd
import random

OUTPUT_PATH = "data/jobs.csv"

jobs = [
    ("Python Developer", "Python, Django, REST API, PostgreSQL", "Build backend APIs using Django and REST framework."),
    ("Backend Engineer", "Python, FastAPI, MongoDB, Redis, Microservices", "Build scalable backend services using FastAPI and microservice architecture."),
    ("AWS Cloud Engineer", "AWS, EC2, S3, IAM, Linux, Docker", "Manage AWS infrastructure and automate deployments."),
    ("DevOps Engineer", "Linux, Docker, Kubernetes, AWS, CI/CD, Jenkins", "Implement CI/CD pipelines and manage containers."),
    ("Data Analyst", "SQL, Excel, Power BI, Python", "Analyze datasets and build dashboards for business reporting."),
    ("Machine Learning Engineer", "Python, ML, NLP, TensorFlow, Pandas", "Develop ML models and deploy training pipelines."),
    ("Java Developer", "Java, Spring Boot, REST API, MySQL", "Develop enterprise backend services using Spring Boot."),
    ("Frontend Developer", "HTML, CSS, JavaScript, React", "Build UI components in React and optimize performance."),
    ("Full Stack Developer", "Python, React, REST API, SQL", "Build full stack apps with backend APIs and frontend UI."),
    ("Data Scientist", "Python, ML, Pandas, Scikit-learn, Statistics", "Create predictive models and analyze large datasets."),
]

locations = ["Bengaluru", "Chennai", "Hyderabad", "Pune", "Mumbai", "Delhi", "Kochi", "Coimbatore"]
experiences = ["0-2", "2-5", "5+"]

companies = ["TCS", "Infosys", "Wipro", "Zoho", "Fractal", "L&T Mindtree", "Tech Mahindra", "Amazon", "Google", "Microsoft"]

rows = []
job_id = 1

for _ in range(50):
    title, skills, desc = random.choice(jobs)
    company = random.choice(companies)
    location = random.choice(locations)
    experience = random.choice(experiences)

    rows.append({
        "job_id": job_id,
        "title": title,
        "company": company,
        "location": location,
        "skills": skills,
        "experience": experience,
        "description": desc
    })
    job_id += 1

df = pd.DataFrame(rows)
df.to_csv(OUTPUT_PATH, index=False)

print(f"✅ Generated {len(df)} jobs into {OUTPUT_PATH}")
