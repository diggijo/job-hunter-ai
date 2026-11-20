# Job Hunter AI

**A personal, AI-powered job discovery and application tracking tool.**

Job Hunter AI is my **first homemade software project**, built from scratch to make my own job search easier to manage. Instead of checking multiple careers pages every day, I wanted one place to discover relevant opportunities, understand how well they match my background, and keep track of applications.

The project brings together automated job collection, AI-assisted matching, and a simple web dashboard.

## What it does

- **Collects job listings** from company careers pages powered by Greenhouse, Ashby, and Lever.
- **Filters opportunities** by technical role, location preferences, seniority, and experience requirements.
- **Evaluates job matches with Google Gemini**, providing a suitability score out of 100, an eligibility assessment, and an explanation of the candidate's strengths and potential gaps.
- **Highlights job requirements**, including programming languages, frameworks, tools, and stated experience.
- **Displays relevant jobs in a local dashboard**, with new listings highlighted and results ordered by match score.
- **Tracks applications**, allowing jobs to be marked as applied or not interested, with a separate view of applied roles.
- **Supports repeat collection runs**, with saved progress, retries for failed job boards, and cached AI evaluations to avoid unnecessary repeat requests.

## How it works

1. Python collectors retrieve postings from Greenhouse, Ashby, and Lever.
2. The listings are normalised and stored in a local SQLite database.
3. Filtering narrows the results to relevant opportunities.
4. Google Gemini assesses candidate suitability and eligibility using the saved candidate profile and job description.
5. A FastAPI web dashboard presents the results and tracks application activity.

## Built with

**Python · FastAPI · SQLite · Google Gemini · Pydantic · HTTPX · Jinja2 · HTML/CSS · PowerShell**

## Why I built it

I started Job Hunter AI as a practical solution to a problem I was facing: searching across different job boards, repeatedly reading similar descriptions, and keeping track of applications was time-consuming.

As my **first self-built project**, it has also been an opportunity to put software engineering skills into practice beyond coursework: working with external APIs, building a database-backed application, developing a web interface, handling failures, and integrating AI into a real workflow.

I'm continuing to improve the accuracy of job matching, the quality of collected descriptions, and the overall experience as I use it.

---

*Personal project — actively developed and improved through real-world use.*
