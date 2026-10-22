from pydantic import BaseModel, Field
from typing import Literal


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
    source_board_id: str | None = None
    external_job_id: str | None = None


class CandidateAnalysis(BaseModel):
    professional_summary: str
    technical_skills: list[str]
    experience_areas: list[str]
    suitable_roles: list[str]
    seniority: str
    education: list[str]
    graduation_year: int | None
    work_authorization: str | None = None


class JobMatchAnalysis(BaseModel):
    score: int = Field(ge=0, le=100)
    eligibility: Literal["eligible", "ineligible", "unknown"]
    eligibility_reasons: list[str]
    strengths: list[str]
    gaps: list[str]
    explanation: str