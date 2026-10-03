from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from app.models import CandidateProfile, Job
from app.database import add_job, get_candidate_profile, get_jobs, initialize_database
from app.matching import get_matching_jobs


app = FastAPI()

templates = Jinja2Templates(directory="app/templates")

initialize_database()


@app.get("/")
def home(request: Request):
    profile = get_candidate_profile()
    jobs = get_jobs()
    matching_jobs = get_matching_jobs(jobs, profile)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "matching_jobs": matching_jobs
        }
    )


@app.get("/profile", response_model=CandidateProfile)
def get_profile():
    return get_candidate_profile()


@app.get("/jobs")
def list_jobs():
    return get_jobs()


@app.get("/jobs/matches")
def list_matching_jobs():
    profile = get_candidate_profile()
    jobs = get_jobs()

    matching_jobs = get_matching_jobs(jobs, profile)

    return {
        "count": len(matching_jobs),
        "jobs": matching_jobs
    }