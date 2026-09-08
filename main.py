import os
import base64
import wave
from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai


# ==============================
# VEXORA TALES AI
# Script + AI Voice Generator
# ==============================

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY secret nahi mila.")

client = genai.Client(api_key=api_key)

# India time ke hisaab se day decide hoga
today = datetime.now(ZoneInfo("Asia/Kolkata"))
day_name = today.strftime("%A")
date_name = today.strftime("%Y-%m-%d")


# ==============================
# CONTENT TYPE
# ==============================

if day_name == "Sunday":

    content_type = "10-Minute YouTube Long Video"

    prompt = """
You are the content creation AI for the YouTube channel "Vexora Tales".

CHANNEL:
- Audience: USA
- Niche: Original viral stories + animated explainers
- Format: Faceless YouTube video
- Language: Natural American English
- Length: Approximately 10 minutes

IMPORTANT:
- Create a completely ORIGINAL story.
- Do not copy any existing YouTube video.
- Do not use copyrighted movie characters or scenes.
- Make the story highly engaging.
- Strong hook in the first 10 seconds.
- Maintain curiosity throughout.
- Make every scene visually easy to animate.
- End with a satisfying conclusion.
- Add a natural YouTube call-to-action.

OUTPUT FORMAT:

TITLE:
Write one clickable but honest title.

HOOK:
Write the opening 10 seconds.

SCENE 1:
VISUAL:
VOICEOVER:

SCENE 2:
VISUAL:
VOICEOVER:

SCENE 3:
VISUAL:
VOICEOVER:

Continue with enough scenes for approximately 10 minutes.

ENDING:
VISUAL:
VOICEOVER:

CALL TO ACTION:
VOICEOVER:
"""

else:

    content_type = "30-Second YouTube Short"

    prompt = """
You are the content creation AI for the YouTube channel "Vexora Tales".

CHANNEL:
- Audience: USA
- Niche: Original viral stories + animated explainers
- Format: Faceless YouTube Short
- Length: Approximately 30 seconds
- Language: Natural American English

IMPORTANT:
- Create a completely ORIGINAL story.
- Do not copy existing YouTube content.
- Do not use copyrighted movie characters or scenes.
- Make the first 2 seconds highly interesting.
- Keep the story fast and easy to understand.
- Create a strong twist or payoff.
- Make visuals easy to animate.
- Add a short natural CTA.

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
VISUAL:
VOICEOVER:

CALL TO ACTION:
VOICEOVER:
"""


# ==============================
# GENERATE STORY
# ==============================

response = client.models.generate_content(
    model="gemini-3.7-flash",
    contents=prompt
)

story = response.text.strip()

if not story:
    raise RuntimeError("Gemini ne story generate nahi ki.")


# ==============================
# SAVE STORY
# ==============================

with open("story.txt", "w", encoding="utf-8") as file:
    file.write(story)


# ==============================
# EXTRACT VOICEOVER
# ==============================

voice_prompt = f"""
You are preparing narration for a professional YouTube video.

Read the following script and extract ONLY the spoken narration.

Rules:
- Include the hook narration.
- Include every scene voiceover.
- Include ending narration.
- Include the call to action narration.
- Remove VISUAL descriptions.
- Do not add speaker names.
- Do not add headings.
- Do not add quotation marks.
- Keep the exact story meaning.
- Natural American English.
- Make it sound like a professional storyteller.

SCRIPT:

{story}
"""

voice_response = client.models.generate_content(
    model="gemini-3.7-flash",
    contents=voice_prompt
)

narration = voice_response.text.strip()

if not narration:
    raise RuntimeError("Voiceover text generate nahi hua.")


with open("narration.txt", "w", encoding="utf-8") as file:
    file.write(narration)


# ==============================
# GEMINI AI VOICE
# ==============================

tts_prompt = f"""
Perform this narration as a professional American YouTube storyteller.

Voice style:
- Male storyteller
- Natural American English
- Clear pronunciation
- Cinematic
- Suspenseful
- Confident
- Medium-fast pacing
- Emotional where appropriate
- No introduction
- No extra words

NARRATION:

{narration}
"""

tts_response = client.interactions.create(
    model="gemini-3.1-flash-tts-preview",
    input=tts_prompt,
    response_format={"type": "audio"},
    generation_config={
        "speech_config": [
            {
                "voice": "Kore"
            }
        ]
    }
)


# ==============================
# SAVE WAV AUDIO
# ==============================

audio_data = base64.b64decode(tts_response.output_audio.data)

with wave.open("voice.wav", "wb") as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(24000)
    wav_file.writeframes(audio_data)


# ==============================
# FINAL LOG
# ==============================

print("=" * 45)
print("VEXORA TALES AI")
print("=" * 45)

print(f"Date: {date_name}")
print(f"Day: {day_name}")
print(f"Content Type: {content_type}")

print("")
print("STORY GENERATED: YES")
print("NARRATION GENERATED: YES")
print("AI VOICE GENERATED: YES")

print("")
print("FILES CREATED:")
print("- story.txt")
print("- narration.txt")
print("- voice.wav")

print("")
print("VEXORA TALES AI VOICE PIPELINE COMPLETE!")
print("=" * 45)
