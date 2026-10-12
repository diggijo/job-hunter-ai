from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    name: str
    preferred_roles: list[str]
    preferred_locations: list[str]


class Job(BaseModel):
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str


class CandidateAnalysis(BaseModel):
    professional_summary: str
    technical_skills: list[str]
    experience_areas: list[str]
    suitable_roles: list[str]
    seniority: str


class JobMatchAnalysis(BaseModel):
    score: int = Field(ge=0, le=100)
    strengths: list[str]
    gaps: list[str]
    explanation: str