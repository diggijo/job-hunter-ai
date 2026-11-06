import re
from app.config import (
    PROGRAMMING_LANGUAGE_PATTERNS,
    FRAMEWORK_TOOL_PATTERNS,
    EXPERIENCE_PATTERNS,
    KEY_REQUIREMENT_PATTERNS,
    KEY_REQUIREMENT_BOUNDARY_PATTERN,
    KEY_REQUIREMENT_START_PATTERN,
    KEY_REQUIREMENT_END_PATTERN,
)
from app.job_filters import is_technical_role


def extract_programming_languages(description: str) -> list[str]:
    if not description:
        return []

    return [
        language
        for language, pattern in PROGRAMMING_LANGUAGE_PATTERNS.items()
        if re.search(pattern, description, re.IGNORECASE)
    ]


def extract_frameworks_tools(description: str) -> list[str]:
    if not description:
        return []

    return [
        tool
        for tool, pattern in FRAMEWORK_TOOL_PATTERNS.items()
        if re.search(pattern, description, re.IGNORECASE)
    ]


def extract_required_experience(description: str) -> list[str]:
    if not description:
        return []

    text = re.sub(r"<[^>]+>", " ", description)
    text = re.sub(r"\s+", " ", text)

    matches = []

    for pattern in EXPERIENCE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start, end = match.span()

            # Ignore matches overlapping an existing requirement.
            if any(start < existing_end and end > existing_start
                   for existing_start, existing_end, _ in matches):
                continue

            matches.append((start, end, match.group(0).strip()))

    return [
        value
        for _, _, value in sorted(matches, key=lambda item: item[0])
    ][:3]


def extract_key_requirements(description: str) -> list[str]:
    if not description:
        return []

    text = re.sub(r"<[^>]+>", " ", description)
    text = re.sub(r"\s+", " ", text).strip()

    # Focus on the requirements section when a clear heading exists.
    start_match = re.search(
        KEY_REQUIREMENT_START_PATTERN, text, re.IGNORECASE
    )

    if start_match:
        text = text[start_match.end():]

    # Stop before optional qualifications or benefits.
    end_match = re.search(
        KEY_REQUIREMENT_END_PATTERN, text, re.IGNORECASE
    )

    if end_match:
        text = text[:end_match.start()]

    requirements = []

    for pattern in KEY_REQUIREMENT_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            requirement = match.group(0).strip(" ,;:-")

            # Stop when the next requirement begins.
            next_requirement = re.search(
                KEY_REQUIREMENT_BOUNDARY_PATTERN,
                requirement,
                re.IGNORECASE,
            )

            if next_requirement:
                requirement = requirement[:next_requirement.start()].strip(" ,;:-")

            if requirement and requirement.lower() not in {
                item.lower() for item in requirements
            }:
                requirements.append(requirement)

    return requirements[:4]


def title_matches(title: str) -> bool:
    return is_technical_role(title)


def location_matches(job_location, preferred_locations=None):
    if not job_location or not preferred_locations:
        return False

    location = job_location.lower().strip()
    preferences = {item.lower().strip() for item in preferred_locations}

    is_remote = "remote" in location

    # Remote positions must explicitly support the UK or Ireland.
    if is_remote:
        if "uk (remote)" in preferences:
            if (
                "united kingdom" in location
                or re.search(r"\buk\b", location)
                or "england" in location
                or "london" in location
            ):
                return True

        if "ireland (remote)" in preferences:
            if "ireland" in location or "dublin" in location:
                return True

        return False

    # On-site and hybrid positions.
    if "ireland" in preferences:
        if "ireland" in location or "dublin" in location:
            return True

    for city in ("london", "new york", "toronto", "boston"):
        if city in preferences and re.search(
            rf"\b{re.escape(city)}\b", location
        ):
            return True

    return False


def get_matching_jobs(jobs, profile):
    matching_jobs = []

    for job in jobs:
        title_match = title_matches(job["title"])

        location_match = location_matches(
            job["location"],
            profile["preferred_locations"]
        )

        if title_match and location_match:
            score, reasons = calculate_job_score(job, profile)

            matching_jobs.append({
                "job": job,
                "score": score,
                "reasons": reasons,
                "programming_languages": extract_programming_languages(
                    job["description"]
                ),
                "frameworks_tools": extract_frameworks_tools(
                    job["description"]
                ),
                "required_experience": extract_required_experience(
                    job["description"]
                ),
                "key_requirements": extract_key_requirements(
                    job["description"]
                )
            })

    matching_jobs.sort(key=lambda match: match["score"], reverse=True)

    return matching_jobs


def calculate_job_score(job, profile):
    reasons = []

    if title_matches(job["title"]):
        reasons.append("Preferred role match")

    if location_matches(job["location"], profile["preferred_locations"]):
        reasons.append("Preferred location match")

    return 0, reasons