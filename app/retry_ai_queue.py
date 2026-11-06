from datetime import datetime, timezone
import time

from filelock import FileLock, Timeout
from google.genai import errors

from app.ai_service import analyse_job_match
from app.config import (
    GEMINI_MODEL,
    GEMINI_REQUEST_DELAY,
)
from app.database import (
    get_ai_evaluation_queue,
    get_candidate_analysis,
    get_job_match_analysis,
    save_job_match_analysis,
    remove_from_ai_evaluation_queue,
    add_to_ai_evaluation_queue,
    get_last_ai_request_time,
    record_ai_request_time,
    record_ai_api_request,
)
from app.models import Job


def retry_ai_queue(candidate_id: int = 1, max_api_calls: int = 10):
    candidate = get_candidate_analysis(candidate_id)

    if candidate is None:
        raise ValueError("No saved candidate analysis found.")

    queued_jobs = get_ai_evaluation_queue(candidate_id)

    print(f"Jobs waiting for evaluation: {len(queued_jobs)}")

    api_calls = 0
    succeeded = 0
    failed = 0

    for job_row in queued_jobs:
        job_id = job_row["job_id"]

        # A previously completed evaluation does not need another API call.
        if get_job_match_analysis(candidate_id, job_id) is not None:
            remove_from_ai_evaluation_queue(job_id)
            continue

        if api_calls >= max_api_calls:
            break

        job = Job(
            title=job_row["title"],
            company=job_row["company"],
            location=job_row["location"],
            description=job_row["description"],
            url=job_row["url"],
            source=job_row["source"],
        )

        last_request_time = get_last_ai_request_time(GEMINI_MODEL)

        if last_request_time is not None:
            elapsed = (
                datetime.now(timezone.utc) - last_request_time
            ).total_seconds()

            remaining_delay = GEMINI_REQUEST_DELAY - elapsed

            if remaining_delay > 0:
                time.sleep(remaining_delay)

        try:
            record_ai_request_time(GEMINI_MODEL)
            api_calls += 1
            record_ai_api_request(GEMINI_MODEL)

            print(
                f"Retrying: "
                f"{job_row['title']} at {job_row['company']}"
            )

            analysis = analyse_job_match(candidate, job)

            save_job_match_analysis(candidate_id, job_id, analysis)
            remove_from_ai_evaluation_queue(job_id)

            succeeded += 1

        except errors.APIError as error:
            failed += 1
            print(f"Gemini API error ({error.code}): {job_row['title']}")

            add_to_ai_evaluation_queue(
                candidate_id, job_id, str(error)
            )

            if error.code == 429:
                print("Gemini quota or rate limit reached. Stopping retries.")
                break

        except Exception as error:
            failed += 1
            print(f"Evaluation failed: {job_row['title']}: {error}")

            add_to_ai_evaluation_queue(
                candidate_id, job_id, str(error)
            )

    print(
        f"\nFinished. Requests: {api_calls}, "
        f"Successful: {succeeded}, Failed: {failed}"
    )


def run_locked_retry(candidate_id: int = 1, max_api_calls: int = 10):
    lock = FileLock("data/ai_evaluation.lock", timeout=0)

    try:
        with lock:
            retry_ai_queue(candidate_id, max_api_calls)
    except Timeout:
        print("Another AI evaluation batch is already running.")


if __name__ == "__main__":
    run_locked_retry(candidate_id=1, max_api_calls=10)