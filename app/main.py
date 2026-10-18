from app.config import EXCLUDED_JOB_KEYWORDS
from app.ai_job_evaluation import meets_experience_requirement
from app.database import add_job, get_candidate_profile, get_jobs, initialize_database, get_job_match_analysis, get_application_statuses, save_application_status, get_application_dates
from app.job_matching import get_matching_jobs
from app.models import CandidateProfile, Job
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import re


app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

initialize_database()


@app.get("/")
def home(request: Request):
    profile = get_candidate_profile()
    jobs = get_jobs()
    matching_jobs = get_matching_jobs(jobs, profile)

    today = datetime.now(ZoneInfo("Europe/Dublin")).date()

    for match in matching_jobs:
        first_seen = match["job"]["first_seen_at"]

        match["is_new_today"] = False

        if first_seen:
            first_seen_utc = datetime.strptime(
                first_seen, "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)

            match["is_new_today"] = (
                first_seen_utc.astimezone(
                    ZoneInfo("Europe/Dublin")
                ).date() == today
            )

    application_statuses = get_application_statuses()

    for match in matching_jobs:
        job = match["job"]
        match["application_status"] = application_statuses.get(
            job["id"],
            "not_applied"
        )

        analysis = get_job_match_analysis(1, job["id"])

        if analysis is not None:
            match["score"] = analysis.score
            match["eligibility"] = analysis.eligibility
            match["strengths"] = analysis.strengths
        else:
            match["score"] = None
            match["eligibility"] = "not_evaluated"
            match["strengths"] = []

    eligibility_priority = {
        "eligible": 0,
        "unknown": 1,
        "not_evaluated": 2,
        "ineligible": 3,
    }

    matching_jobs = [
        match for match in matching_jobs
        if match["application_status"] == "not_applied"
        and match["score"] is not None
        and match["score"] >= 70
        and meets_experience_requirement(match["job"]["description"])
        and not EXCLUDED_JOB_KEYWORDS.intersection(
            re.findall(r"[a-z]+", match["job"]["title"].lower())
        )
    ]

    matching_jobs.sort(
        key=lambda match: (
            match["score"] is None,
            -(match["score"] if match["score"] is not None else 0),
        )
    )
    
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


@app.post("/jobs/{job_id}/application-status")
def update_application_status(
    job_id: int,
    status: str = Body(embed=True)
):
    if not any(job["id"] == job_id for job in get_jobs()):
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        save_application_status(job_id, status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid application status"
        )

    return {
        "job_id": job_id,
        "status": status,
        "saved": True
    }


def format_application_date(timestamp):
    if not timestamp:
        return None

    utc_date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    utc_date = utc_date.replace(tzinfo=timezone.utc)

    irish_date = utc_date.astimezone(ZoneInfo("Europe/Dublin"))

    return irish_date.strftime("%d %B %Y").lstrip("0")


@app.get("/applied")
def applied_jobs(request: Request):
    application_statuses = get_application_statuses()
    application_dates = get_application_dates()
    applied_matches = []

    for job in get_jobs():
        if application_statuses.get(job["id"]) != "applied":
            continue

        analysis = get_job_match_analysis(1, job["id"])

        applied_matches.append({
            "job": dict(job),
            "score": analysis.score if analysis else None,
            "eligibility": analysis.eligibility if analysis else "not_evaluated",
            "application_status": "applied",
            "reasons": [],
            "applied_on": format_application_date(application_dates.get(job["id"])),
        })

    applied_matches.sort(
        key=lambda match: match["score"] if match["score"] is not None else -1,
        reverse=True,
    )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"matching_jobs": applied_matches},
    )


