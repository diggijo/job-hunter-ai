# Job Hunter AI

**AI-powered job discovery, matching, and application tracking.**

Job Hunter AI is a personal Python project that collects software, data, and AI job postings from multiple applicant tracking systems (ATS), evaluates their suitability using Google Gemini, and displays the results in a local web dashboard.

> **Project status:** Actively developed, local-first application. Currently built around a single configured candidate profile rather than a hosted multi-user platform.

## Features

- **Multi-source job collection** from Greenhouse, Ashby, and Lever.
- **Automatic filtering** by technical role, preferred location, job seniority, and stated experience requirements.
- **AI job matching** using Gemini, with a score out of 100, an eligibility assessment, strengths, gaps, and an explanation.
- **Job requirement extraction** for programming languages, frameworks, tools, required experience, and key requirements.
- **Application tracking** for applied and not-interested jobs, plus a separate applied-jobs view.
- **Incremental, batched collection** with provider-specific progress files and retry handling for failed boards.
- **Cached AI evaluations** in SQLite to reduce redundant model requests.
- **Local FastAPI dashboard** built using Jinja2 templates.

## Tech stack

| Component | Technology |
| --- | --- |
| Backend and web server | Python, FastAPI, Uvicorn |
| Templates | Jinja2 |
| Database | SQLite |
| AI evaluation | Google Gemini (`google-genai`) |
| HTTP clients | HTTPX |
| Validation | Pydantic |
| PDF text extraction | PyMuPDF |
| Automation | Python, PowerShell, Windows batch scripts |

## How it works

```text
Greenhouse ─┐
Ashby ──────┼──> Collect & normalise postings ──> SQLite
Lever ──────┘                                       |
                                                   v
                                Filter by role, location & experience
                                                   |
                                                   v
                                 Gemini match & eligibility analysis
                                                   |
                                                   v
                                    Cached results in SQLite
                                                   |
                                                   v
                                    FastAPI dashboard & tracking
```

The collectors use the ATS APIs to retrieve public postings. The Lever integration combines plain-text fields, HTML fallbacks, structured sections, and additional content to preserve job requirements.

Gemini evaluates the full saved job description against a candidate profile. Dashboard fields such as programming languages and key requirements are extracted separately using rule-based patterns.

## Getting started

### Requirements

- Python 3.11 or newer recommended
- A Gemini API key for AI evaluation
- Windows/PowerShell for the included launcher scripts (the Python modules can be invoked in other environments)

### 1. Clone the repository

```powershell
git clone https://github.com/diggijo/job-hunter-ai.git
cd job-hunter-ai

py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

The repository currently has no committed `requirements.txt` or `pyproject.toml`. Install the direct runtime dependencies:

```powershell
python -m pip install fastapi uvicorn jinja2 httpx pydantic python-dotenv google-genai pymupdf filelock
```

Pinning dependencies in a requirements file is a planned improvement.

### 3. Configure the Gemini API key

Create a `.env` file in the repository root:

```dotenv
GENAI_API_KEY=your_gemini_api_key
```

**Do not commit `.env` or API credentials.** Collecting public job postings does not require Gemini, but AI evaluation does.

### 4. Prepare candidate and board data

The app uses `data/jobhunter.db` as its local SQLite database. Starting the FastAPI app creates the database tables, but **does not automatically create the candidate profile or candidate AI analysis**. The dashboard and evaluator expect these records to exist.

This is currently a personal project without a complete first-run onboarding flow. To set up a fresh installation, review the candidate models and persistence functions in `app/models.py`, `app/database.py`, and `app/ai_service.py`. The repository also includes job-board import utilities and board source lists in `data/`.

### 5. Start the dashboard

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Visit **http://127.0.0.1:8000/**.

A `launch_job_hunter.bat` convenience launcher is included. It contains a developer-specific absolute path, so update the path to match your clone before using it.

## Usage

### Collect jobs

```powershell
python -m app.run_full_collection
```

This collects from Greenhouse, Ashby, and Lever in batches, saves each provider's progress, and retries previously failed boards at the end.

To retry failed collection boards independently:

```powershell
python -m app.collect_batches --retry-failed
```

### Run AI job evaluation

```powershell
python -m app.run_daily_ai
```

**This command makes Gemini API requests**, subject to the evaluator's configured request limits and delays. Gemini API usage may incur costs or quota consumption.

For a dry run that makes no Gemini requests:

```powershell
python -m app.run_daily_ai --dry-run
```

The included `run_daily_ai.bat` runs collection and then AI evaluation, logging activity to `logs/daily_ai.log`. Update its machine-specific path before use.

### Manage preferred locations

```powershell
python -m app.manage_preferences
```

Alternatively, use `app/commands/manage_preferences.ps1`.

### Check and retry failed AI evaluations

```powershell
.\app\commands\check_queue.ps1
.\app\commands\retry_queue.ps1
```

Checking the queue is read-only. The retry script asks for confirmation before making Gemini requests.

## Dashboard and endpoints

| Route | Purpose |
| --- | --- |
| `GET /` | View filtered, ranked job recommendations |
| `GET /applied` | View jobs marked as applied |
| `POST /jobs/{job_id}/application-status` | Update a job's application status |

The dashboard displays AI scores, eligibility, extracted requirements, job links, and application actions. A *New Today* label highlights recently discovered postings.

Filtering thresholds and patterns, such as `MIN_MATCH_SCORE`, `MAX_REQUIRED_EXPERIENCE`, and excluded seniority keywords, can be configured in `app/config.py`.

## Project structure

```text
app/
  collectors/                # Greenhouse, Ashby & Lever collectors
  commands/                  # PowerShell helpers
  static/                    # Dashboard CSS and other assets
  templates/                 # Jinja2 templates
  main.py                    # FastAPI routes and views
  config.py                  # Matching and collection configuration
  database.py                # SQLite schema and persistence
  models.py                  # Pydantic models
  ai_service.py              # Gemini interaction and prompts
  ai_job_evaluation.py       # Matching and AI evaluation pipeline
  job_filters.py             # Technical role and location filtering
  job_matching.py            # Requirement extraction
  collect_batches.py         # Batched provider collection & retries
  run_full_collection.py     # Collection orchestration
  run_daily_ai.py            # AI evaluation entry point
  retry_ai_queue.py          # Failed evaluation retries
  repair_lever_descriptions.py # Targeted legacy description repair
candidate/                   # Candidate files (gitignored)
data/                        # Board lists, progress and local database
launch_job_hunter.bat         # Windows dashboard launcher
run_daily_ai.bat              # Windows collection + AI launcher
```

## Data, privacy, and API usage

Job Hunter AI runs locally but contacts external ATS APIs to collect jobs. When Gemini evaluation is invoked, job descriptions and candidate information are sent to Google's API. Only provide information you are comfortable processing through those services.

Keep `.env`, CVs, database files, local backups, and sensitive logs out of Git. The existing `.gitignore` excludes `.env`, `data/*.db`, and candidate documents; review other generated files before committing.

AI match scores and eligibility labels are screening aids, **not hiring guarantees or verified legal immigration advice**.

## Current limitations

- Fresh installations require manual candidate profile and AI-analysis setup.
- No committed dependency manifest or automated test suite is documented yet.
- Windows launcher scripts contain machine-specific paths.
- Regex-based requirement extraction can miss or truncate unusual wording.
- The application currently assumes a single local candidate profile.

## License

No license file is currently included. A public GitHub repository does not, by itself, grant permission to reuse or redistribute the code.
