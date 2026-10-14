# AI configuration
JOB_MATCH_CACHE_VERSION = 2


# Target job locations
TARGET_LOCATIONS = [
    "Dublin",
    "London",
    "UK (Remote)",
    "Ireland (Remote)"
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

MAX_REQUIRED_EXPERIENCE = 3


# Gemini model used to evaluate job eligibility and candidate match scores.
GEMINI_MODEL = "gemini-3.5-flash-lite"

# Maximum Gemini API requests our job hunter can make per day.
# Set below the free-tier allowance of 500 to leave a safety buffer.
DAILY_AI_LIMIT = 475

# Minimum delay in seconds between Gemini evaluation requests.
GEMINI_REQUEST_DELAY = 5