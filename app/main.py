from fastapi import FastAPI
from pydantic import BaseModel

class CandidateProfile(BaseModel):
    name: str
    preferred_roles: list[str]
    preferred_locations: list[str]

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Job Hunter AI is running!"}

@app.get("/profile", response_model=CandidateProfile)
def get_profile():
    profile = CandidateProfile(
        name="Joseph Diggins",
        preferred_roles=[
            "Software Engineer",
            "Gameplay Programmer",
            "Machine Learning Engineer",
            "Unity Developer"
        ],
        preferred_locations=[
            "Ireland",
            "London",
            "New York",
            "Remote"
        ]
    )
    return profile