# AI configuration
JOB_MATCH_CACHE_VERSION = 2

# Target Job Titles
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


# Job titles to exclude
EXCLUDED_JOB_KEYWORDS = {
    "intern",
    "internship",
    "senior",
    "staff",
    "sr",
    "principal",
    "lead",
    "research",
    "researcher",
    "expert",
    "vice",
    "president",
    "director",
    "head",
    "manager"
}


# Job titles to prioritise
PREFERRED_JOB_KEYWORDS = {
    "junior",
    "graduate",
    "entry-level",
    "entry level",
    "associate",
    "software engineer I",
    "software developer I"
}

# Experience Required
EXPERIENCE_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10
}


MAX_REQUIRED_EXPERIENCE = 2


# Gemini model used to evaluate job eligibility and candidate match scores.
GEMINI_MODEL = "gemini-3.5-flash-lite"


# Minimum delay in seconds between Gemini evaluation requests.
GEMINI_REQUEST_DELAY = 5


BATCH_SIZE = 25
MAX_WORKERS = 4
BATCH_DELAY_SECONDS = 2

MIN_MATCH_SCORE = 70