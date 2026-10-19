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