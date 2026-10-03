def title_matches(job_title, preferred_roles):
    job_title = job_title.lower()

    for role in preferred_roles:
        if role.lower() in job_title:
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
            matching_jobs.append(job)

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