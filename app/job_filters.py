import re


TECHNICAL_ROLE_PATTERNS = [
    # Software development
    r"\bsoftware (engineer|developer)\b",
    r"\b(back.?end|front.?end|full.?stack) (engineer|developer)\b",
    r"\b(application|web|mobile) developer\b",
    r"\b(python|java|javascript|typescript|c\+\+|\.net) developer\b",

    # Game development
    r"\b(game|games|gameplay|engine) (developer|engineer|programmer)\b",
    r"\b(unity|unreal) (developer|engineer|programmer)\b",

    # Data and analytics
    r"\bdata (engineer|analyst|scientist)\b",
    r"\b(analytics|business intelligence|bi) (engineer|analyst|developer)\b",

    # AI and machine learning
    r"\b(machine learning|ml|ai|computer vision) (engineer|developer|scientist)\b",

    # Cloud and infrastructure
    r"\b(cloud|platform|devops|infrastructure|site reliability) engineer\b",
    r"(?<!noc engineer / )\bsre\b",

    # Testing and automation
    r"\b(qa|test automation|automation|quality assurance) engineer\b",
    r"\bsoftware (tester|test engineer)\b",
    r"\bsdet\b",

    # Other relevant technical roles
    r"\bbusiness systems analyst\b",
    r"\b(integration|embedded|firmware) engineer\b",
]


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