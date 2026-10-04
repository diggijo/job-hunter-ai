import re


def title_matches(job_title, preferred_roles):
    job_title = job_title.lower()

    for role in preferred_roles:
        pattern = rf"\b{re.escape(role.lower())}\b"

        if re.search(pattern, job_title):
            return True

    return False


def location_matches(job_location, preferred_locations):
    job_location = job_location.lower()

    for preferred_location in preferred_locations:
        preferred_location = preferred_location.lower()

        locations = LOCATION_ALIASES.get(
            preferred_location,
            [preferred_location]
        )
    
        for location in locations:
            if location.lower() in job_location:
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


LOCATION_ALIASES = {
    "ireland": [
        "ireland",
        "dublin",
        "cork",
        "galway",
        "limerick"
    ],
    "new york": [
        "new york",
        "nyc"
    ],
    "london": [
        "london"
    ],
    "remote": [
        "remote"
    ]
}

SENIORITY_PENALTIES = {
    "senior": 20,
    "staff": 30,
    "principal": 40,
    "lead": 30,
    "director": 50
}

EARLY_CAREER_BONUSES = {
    "graduate": 20,
    "junior": 15,
    "entry": 15,
    "intern": 10
}

def calculate_job_score(job, profile):
    score = 0
    reasons = []

    if title_matches(
        job["title"],
        profile["preferred_roles"]
    ):
        score += 50
        reasons.append("Preferred role match")

    if location_matches(
        job["location"],
        profile["preferred_locations"]
    ):
        score += 50
        reasons.append("Preferred location match")

    job_title = job["title"].lower()

    for seniority, penalty in SENIORITY_PENALTIES.items():
        if seniority in job_title:
            score -= penalty
            reasons.append(f"{seniority.title()} level role")

    for career_level, bonus in EARLY_CAREER_BONUSES.items():
        if career_level in job_title:
            score += bonus
            reasons.append(f"{career_level.title()} role")

    return score, reasons