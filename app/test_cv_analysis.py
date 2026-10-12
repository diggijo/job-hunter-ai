from app.cv_reader import extract_cv_text
from app.ai_service import analyse_cv
from app.database import (
    initialize_database,
    save_candidate_analysis,
    get_candidate_analysis
)


candidate_id = 1

initialize_database()

analysis = get_candidate_analysis(candidate_id)

if analysis is None:
    print("No saved analysis found. Calling Gemini...")

    cv_path = "candidate/Joseph-Diggins-CV.pdf"
    cv_text = extract_cv_text(cv_path)

    analysis = analyse_cv(cv_text)

    save_candidate_analysis(candidate_id, analysis)

else:
    print("Using saved candidate analysis.")

print(analysis.model_dump_json(indent=2))