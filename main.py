import os
from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai


# Gemini API key
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY secret nahi mila.")


# Gemini client
client = genai.Client(api_key=api_key)


# India time ke hisaab se aaj ka din
today = datetime.now(ZoneInfo("Asia/Kolkata"))
day_name = today.strftime("%A")


# Sunday = Long Video
if day_name == "Sunday":

    prompt = """
You are the content creation AI for the YouTube channel "Vexora Tales".

CHANNEL:
- Audience: USA
- Niche: Viral original stories + animated explainers
- Format: Faceless YouTube video
- Video length: approximately 10 minutes
- Language: natural American English

Create ONE completely original YouTube video.

IMPORTANT:
- Do not copy any existing YouTube video or story.
- Do not use copyrighted characters, movie scenes, or copyrighted clips.
- Create an original and engaging concept.
- Make the first 10 seconds extremely interesting.
- Keep the story easy to understand.
- Maintain strong curiosity throughout the video.
- Include a satisfying ending.
- Add a natural call to action at the end.

OUTPUT FORMAT:

TITLE:
Write one clickable but honest title.

HOOK:
Write the opening hook for the first 10 seconds.

SCENE 1:
VISUAL:
VOICEOVER:

SCENE 2:
VISUAL:
VOICEOVER:

SCENE 3:
VISUAL:
VOICEOVER:

Continue with enough scenes to create approximately 10 minutes of narration.

At the end include:

ENDING:
CALL TO ACTION:
"""


# Monday-Saturday = Short
else:

    prompt = """
You are the content creation AI for the YouTube channel "Vexora Tales".

CHANNEL:
- Audience: USA
- Niche: Viral original stories + animated explainers
- Format: Faceless YouTube Short
- Video length: approximately 30 seconds
- Language: natural American English

Create ONE completely original YouTube Short.

IMPORTANT:
- Do not copy any existing YouTube video or story.
- Do not use copyrighted characters, movie scenes, or copyrighted clips.
- Create an original and engaging concept.
- Make the first 2 seconds very strong.
- Keep the story fast and interesting.
- Build curiosity quickly.
- Give the viewer a satisfying ending.
- Add a short call to action.

OUTPUT FORMAT:

TITLE:
Write one clickable but honest title.

HOOK:
Write the opening hook.

SCENE 1:
VISUAL:
VOICEOVER:

SCENE 2:
VISUAL:
VOICEOVER:

SCENE 3:
VISUAL:
VOICEOVER:

SCENE 4:
VISUAL:
VOICEOVER:

ENDING:
CALL TO ACTION:
"""


# Generate the content with Gemini
response = client.models.generate_content(
    model="gemini-3.7-flash",
    contents=prompt
)


# Show result
print("====================================")
print("VEXORA TALES AI")
print("====================================")
print("Date:", today.strftime("%Y-%m-%d"))
print("Day:", day_name)

if day_name == "Sunday":
    print("Content Type: 10-Minute Long Video")
else:
    print("Content Type: 30-Second YouTube Short")

print("====================================")
print()
print(response.text)
