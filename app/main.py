from fastapi import FastAPI
from app.database import get_candidate_profile


app = FastAPI()

@app.get("/")
def home():
    return {"message": "Job Hunter AI is running!"}

@app.get("/profile")
def get_profile():
    return get_candidate_profile()