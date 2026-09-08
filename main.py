
import os
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY secret nahi mila.")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-3.7-flash",
    contents="Give me one short original YouTube video idea for a USA audience."
)

print("Vexora Tales AI is running!")
print("AI Video Idea:")
print(response.text)
