from fastapi import FastAPI
from app.models import CandidateProfile
from app.database import get_candidate_profile, initialize_database


app = FastAPI()

initialize_database()


@app.get("/")
def home():
    return {"message": "Job Hunter AI is running!"}


@app.get("/profile", response_model=CandidateProfile)
def get_profile():
    return get_candidate_profile()