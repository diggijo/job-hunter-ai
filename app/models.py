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