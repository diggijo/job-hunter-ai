from pydantic import BaseModel


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