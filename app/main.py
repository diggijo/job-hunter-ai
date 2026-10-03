from fastapi import FastAPI, HTTPException
from app.models import CandidateProfile, Job
from app.database import add_job, get_candidate_profile, get_jobs, initialize_database


app = FastAPI()

initialize_database()


@app.get("/")
def home():
    return {"message": "Job Hunter AI is running!"}


@app.get("/profile", response_model=CandidateProfile)
def get_profile():
    return get_candidate_profile()

@app.post("/jobs")
def create_job(job: Job):
    added = add_job(job)

    if not added:
        raise HTTPException(
            status_code=409,
            detail="Job with this URL already exists."
        )
    
    return {"message": "Job added successfully!"}


@app.get("/jobs")
def list_jobs():
    return get_jobs()