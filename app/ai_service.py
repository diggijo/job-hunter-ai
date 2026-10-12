import os

from app.models import CandidateAnalysis
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