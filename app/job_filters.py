import re
from app.config import TECHNICAL_ROLE_PATTERNS


def is_technical_role(title: str) -> bool:
    return any(
        re.search(pattern, title, re.IGNORECASE)
        for pattern in TECHNICAL_ROLE_PATTERNS
    )


def get_job_priority(title: str) -> int:
    title = title.lower()

    early_career_patterns = [
        r"\bgraduate\b",
        r"\bnew grad\b",
        r"\bjunior\b",
        r"\bentry.level\b",
        r"\bsoftware engineer i\b",
    ]

    if any(re.search(pattern, title) for pattern in early_career_patterns):
        return 1

    specialised_patterns = [
        r"\bdevops\b",
        r"\bsite reliability\b",
        r"\bsre\b",
        r"\bcloud\b",
        r"\binfrastructure\b",
        r"\bplatform engineer\b",
    ]

    if any(re.search(pattern, title) for pattern in specialised_patterns):
        return 3

    return 2


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
