import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

from filelock import FileLock
from google.genai import errors

from app.ai_service import analyse_job_match
from app.config import GEMINI_MODEL, DAILY_AI_LIMIT, GEMINI_REQUEST_DELAY
from app.database import (
    get_candidate_analysis,
    get_jobs,
    get_application_statuses,
    get_daily_ai_usage,
    record_ai_api_request,
    get_last_ai_request_time,
    record_ai_request_time,
    save_job_match_analysis,
)
from app.models import Job

CANDIDATE_ID = 1

backups = sorted(Path("data").glob("work_authorization_backup_*.json"))
if not backups:
    sys.exit("No work authorization backup found.")

backup_path = backups[-1]
progress_path = backup_path.with_suffix(".progress.json")

original = json.loads(backup_path.read_text(encoding="utf-8"))

if len(original) != 32:
    sys.exit(f"Expected 32 jobs, found {len(original)}.")

candidate = get_candidate_analysis(CANDIDATE_ID)
if candidate is None or not candidate.work_authorization:
    sys.exit("Candidate work authorization is missing.")

jobs = {row["id"]: row for row in get_jobs()}

completed = {}
if progress_path.exists():
    completed = json.loads(progress_path.read_text(encoding="utf-8"))

def save_progress():
    progress_path.write_text(
        json.dumps(completed, indent=2),
        encoding="utf-8",
    )

print(f"Using backup: {backup_path}")
print(f"Already completed: {len(completed)}")
print(f"Jobs in backup: {len(original)}")

with FileLock("data/ai_evaluation.lock", timeout=0):
    for item in original:
        job_id = item["job_id"]
        key = str(job_id)

        if key in completed:
            continue

        statuses = get_application_statuses()
        status = statuses.get(job_id, "not_applied")

        if status != "not_applied":
            print(f"Skipping {job_id}: {status}", flush=True)
            continue

        row = jobs.get(job_id)
        if row is None:
            print(f"Skipping {job_id}: job no longer exists", flush=True)
            continue

        usage = get_daily_ai_usage(GEMINI_MODEL)
        if usage >= DAILY_AI_LIMIT:
            print("Daily Gemini limit reached. Run again tomorrow.")
            break

        job = Job(
            title=row["title"],
            company=row["company"],
            location=row["location"],
            description=row["description"],
            url=row["url"],
            source=row["source"],
        )

        last_request = get_last_ai_request_time(GEMINI_MODEL)
        if last_request is not None:
            elapsed = (
                datetime.now(timezone.utc) - last_request
            ).total_seconds()
            remaining = GEMINI_REQUEST_DELAY - elapsed
            if remaining > 0:
                time.sleep(remaining)

        record_ai_api_request(GEMINI_MODEL)
        record_ai_request_time(GEMINI_MODEL)

        print(
            f"\nReevaluating {job_id}: {row['company']} | {row['title']}",
            flush=True,
        )

        try:
            analysis = analyse_job_match(candidate, job)
        except errors.APIError as error:
            print(f"Gemini API error: {error}", flush=True)
            break
        except Exception as error:
            print(f"Evaluation failed: {error}", flush=True)
            break

        save_job_match_analysis(CANDIDATE_ID, job_id, analysis)

        old = item["analysis"]
        completed[key] = {
            "company": row["company"],
            "title": row["title"],
            "old_score": old["score"],
            "new_score": analysis.score,
            "old_eligibility": old["eligibility"],
            "new_eligibility": analysis.eligibility,
        }
        save_progress()

        print(
            f"Score: {old['score']} -> {analysis.score} | "
            f"Eligibility: {old['eligibility']} -> {analysis.eligibility}",
            flush=True,
        )

print(f"\nCompleted reevaluations: {len(completed)}/32")
print(f"Progress saved to: {progress_path}")
