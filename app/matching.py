import re
from app.config import TARGET_LOCATIONS
from app.job_filters import is_technical_role


def title_matches(title: str, preferred_roles=None) -> bool:
    return is_technical_role(title)


def location_matches(job_location, preferred_locations=None):
    location = job_location.lower().strip()

    for target in TARGET_LOCATIONS:
        target = target.lower()

        if target == "dublin" and "dublin" in location:
            return True

        if target == "london" and "london" in location:
            return True

        if target == "uk (remote)":
            if "remote" in location and (
                "united kingdom" in location
                or re.search(r"\buk\b", location)
            ):
                return True

        if target == "ireland (remote)":
            if "remote" in location and "ireland" in location:
                return True

    return False


def get_matching_jobs(jobs, profile):
    matching_jobs = []

    for job in jobs:
        title_match = title_matches(
            job["title"],
            profile["preferred_roles"]
        )

        location_match = location_matches(
            job["location"],
            profile["preferred_locations"]
        )

        if title_match and location_match:
            score, reasons = calculate_job_score(job, profile)

            matching_jobs.append({
                "job": job,
                "score": score,
                "reasons": reasons
            })

    matching_jobs.sort(key=lambda match: match["score"], reverse=True)

    return matching_jobs


def calculate_job_score(job, profile):
    reasons = []

    if title_matches(job["title"], profile["preferred_roles"]):
        reasons.append("Preferred role match")

    if location_matches(job["location"], profile["preferred_locations"]):
        reasons.append("Preferred location match")

    return 0, reasons