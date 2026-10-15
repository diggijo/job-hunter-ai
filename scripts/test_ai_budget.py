from app.config import GEMINI_MODEL, DAILY_AI_LIMIT
from app.database import get_daily_ai_usage


used = get_daily_ai_usage(GEMINI_MODEL)
remaining = max(0, DAILY_AI_LIMIT - used)

print(f"Gemini model: {GEMINI_MODEL}")
print(f"Daily budget: {DAILY_AI_LIMIT}")
print(f"Requests used: {used}")
print(f"Requests remaining: {remaining}")
