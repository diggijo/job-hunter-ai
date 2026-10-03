from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from app.models import CandidateProfile, Job
from app.database import add_job, get_candidate_profile, get_jobs, initialize_database
from app.matching import get_matching_jobs


app = FastAPI()

initialize_database()


@app.get("/", response_class=HTMLResponse)
def home():
    profile = get_candidate_profile()
    jobs = get_jobs()
    matching_jobs = get_matching_jobs(jobs, profile)

    job_html = ""

    for job in matching_jobs:
        job_html += f"""
            <div>
                <h3>{job["title"]}</h3>
                <p>{job["company"]} - {job["location"]}</p>
                <a href="{job["url"]}" target="_blank">View Job</a>
            </div>
            <hr>
        """

    return f"""
    <html>
        <head>
            <title>Job Hunter AI</title>
        </head>
        <body>
            <h1>Job Hunter AI</h1>
            <p>{len(matching_jobs)} potential jobs found</p>

            {job_html}
        </body>
    </html>
    """


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