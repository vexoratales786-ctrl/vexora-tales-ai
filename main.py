import os
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY secret nahi mila.")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-3.7-flash",
    contents="Create one original 30-second YouTube Shorts story idea for a USA audience. Give only the idea."
)

print("Vexora Tales AI is running!")
print("AI Story Idea:")
print(response.text)
