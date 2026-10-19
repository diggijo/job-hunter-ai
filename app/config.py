# AI configuration
JOB_MATCH_CACHE_VERSION = 2


# Target job locations
TARGET_LOCATIONS = [
    "Dublin",
    "London",
    "UK (Remote)",
    "Ireland (Remote)"
]


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


# Maximum Gemini API requests our job hunter can make per day.
# Set below the free-tier allowance of 500 to leave a safety buffer.
DAILY_AI_LIMIT = 475


# Minimum delay in seconds between Gemini evaluation requests.
GEMINI_REQUEST_DELAY = 5


PROGRAMMING_LANGUAGE_PATTERNS = {
    "C#": r"(?<!\w)C#(?!\w)",
    "C++": r"(?<!\w)C\+\+(?!\w)",
    "Python": r"\bPython\b",
    "Java": r"\bJava\b",
    "JavaScript": r"\bJavaScript\b",
    "TypeScript": r"\bTypeScript\b",
    "Go": r"\bGolang\b|\bGo programming\b|\bGo\b", 
    "Rust": r"\bRust\b",
    "Ruby": r"\bRuby\b",
    "PHP": r"\bPHP\b",
    "Kotlin": r"\bKotlin\b",
    "Swift": r"\bSwift\b",
    "SQL": r"\bSQL\b",
}

FRAMEWORK_TOOL_PATTERNS = {
    "React": r"\bReact(?:\.js)?\b",
    "Angular": r"\bAngular\b",
    "Vue.js": r"\bVue(?:\.js)?\b",
    "Node.js": r"\bNode(?:\.js)?\b",
    "Next.js": r"\bNext\.js\b",
    ".NET": r"(?<!\w)\.NET\b",
    "ASP.NET": r"\bASP\.NET\b",
    "FastAPI": r"\bFastAPI\b",
    "Django": r"\bDjango\b",
    "Flask": r"\bFlask\b",
    "Spring Boot": r"\bSpring Boot\b",
    "AWS": r"\bAWS\b",
    "Azure": r"\bAzure\b",
    "Google Cloud": r"\bGCP\b|\bGoogle Cloud\b",
    "Docker": r"\bDocker\b",
    "Kubernetes": r"\bKubernetes\b|\bK8s\b",
    "PostgreSQL": r"\bPostgreSQL\b|\bPostgres\b",
    "MongoDB": r"\bMongoDB\b",
    "Git": r"\bGit\b",
    "CI/CD": r"\bCI/CD\b",
}


EXPERIENCE_PATTERNS = [
    r"\b(?:at least|minimum of|minimum|over)\s+\d+\+?\s+years?\b",
    r"\b\d+\s*\+\s*years?\b",
    r"\b\d+\s*(?:-|–|to)\s*\d+\s+years?\b",
    r"\b\d+\s+years?\s+(?:of\s+)?(?:professional|commercial|relevant|hands-on|software|development|engineering|work)?\s*experience\b",
]


KEY_REQUIREMENT_PATTERNS = [
    r"\b\d+\s*[-–]\s*\d+\s+years?\s+of\s+[\w\s]+",
    r"\b(?:proficiency|experience|familiarity)\s+(?:in|with)\s+[^.!?]{10,300}",
    r"\b(?:strong|solid|good)\s+(?:foundational\s+)?"
    r"(?:knowledge|understanding)\s+of\s+[^.!?]{10,300}",
    r"\bability\s+to\s+[^.!?]{10,300}",
]


KEY_REQUIREMENT_BOUNDARY_PATTERN = (
    r"\s+(?=(?:Strong|Solid|Good)\s+(?:foundational\s+)?"
    r"(?:knowledge|understanding)\b|"
    r"Proficiency\s+(?:in|with)\b|"
    r"Experience\s+(?:in|with)\b|"
    r"Familiarity\s+(?:in|with)\b|"
    r"Ability\s+to\b|"
    r"Exceptional\s+attention\b)"
)


KEY_REQUIREMENT_START_PATTERN = (
    r"\b(?:what you will need in this role|requirements|"
    r"qualifications|what we are looking for|must have)\b"
)


KEY_REQUIREMENT_END_PATTERN = (
    r"\b(?:additional skills or experience|nice to have|"
    r"preferred qualifications|benefits|what we offer)\b"
)