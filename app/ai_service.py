import os

from app.models import CandidateAnalysis, Job, JobMatchAnalysis
from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))


def analyse_cv(cv_text: str) -> CandidateAnalysis:
    prompt = f"""
        Analyse the following CV for an AI-powered job search application.

        Extract:
        - A concise professional summary
        - Technical skills explicitly supported by the CV
        - Areas of professional and project experience
        - The candidate's approximate seniority level

        Identify a broad range of suitable job titles based on the
        candidate's education, technical skills, professional experience,
        and projects.

        Consider:
        - Different industry naming conventions
        - Graduate, junior, and associate positions
        - Related roles where the candidate has transferable skills
        - Specialisations supported by the candidate's background

        Do not restrict suitable roles to titles explicitly mentioned
        in the CV.

        Do not invent qualifications, skills, or experience.
        Do not recommend roles requiring substantial experience
        beyond the candidate's background.

        CV:
        {cv_text}
        """

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CandidateAnalysis
        )
    )

    return CandidateAnalysis.model_validate_json(response.text)


def analyse_job_match(
    candidate: CandidateAnalysis,
    job: Job
) -> JobMatchAnalysis:

    prompt = f"""
        You are evaluating how suitable a job opportunity is for a candidate.

        CANDIDATE PROFILE:
        {candidate.model_dump_json(indent=2)}

        JOB TITLE:
        {job.title}

        COMPANY:
        {job.company}

        JOB LOCATION:
        {job.location}

        JOB DESCRIPTION:
        {job.description}

        Evaluate the candidate's suitability for this specific job.

        Consider:
        - Technical skills and technologies
        - Relevant professional and project experience
        - Seniority and years of experience required
        - Transferable skills
        - Important missing qualifications or experience

        Provide:
        - A suitability score between 0 and 100
        - Specific strengths supported by the candidate profile
        - Important gaps relative to the job requirements
        - A concise explanation of the overall assessment

        Scoring guidance:
        90-100: Exceptional match with nearly all major requirements
        75-89: Strong match with some minor gaps
        60-74: Reasonable match with meaningful gaps
        40-59: Partial match with significant gaps
        0-39: Poor match or substantially underqualified

        Do not invent candidate qualifications.
        Do not assume that missing experience is present.
        Do not treat a matching job title alone as evidence of suitability.
        Treat mandatory qualifications and seniority requirements seriously.
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=JobMatchAnalysis
        )
    )

    return JobMatchAnalysis.model_validate_json(response.text)