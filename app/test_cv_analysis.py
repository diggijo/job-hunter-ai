from app.cv_reader import extract_cv_text
from app.ai_service import analyse_cv


cv_path = "candidate/Joseph-Diggins-CV.pdf"

cv_text = extract_cv_text(cv_path)

analysis = analyse_cv(cv_text)

print(analysis.model_dump_json(indent=2))