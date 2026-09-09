import os
import base64
import time
import wave
from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai


# ==========================================
# VEXORA TALES AI
# ==========================================

CHANNEL_NAME = "Vexora Tales"
TARGET_AUDIENCE = "USA"
TIMEZONE = "Asia/Kolkata"

TEXT_MODEL = gemini-3.7-flash
TTS_MODEL = "gemini-3.1-flash-tts-preview"

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY secret nahi mila.")

client = genai.Client(api_key=api_key)


# ==========================================
# RETRY SYSTEM
# ==========================================

def retry_call(function, max_attempts=3):
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return function()

        except Exception as error:
            last_error = error

            print(
                f"Gemini request failed "
                f"(attempt {attempt}/{max_attempts})"
            )

            if attempt < max_attempts:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    raise last_error


# ==========================================
# DATE / DAY
# ==========================================

today = datetime.now(ZoneInfo(TIMEZONE))

day_name = today.strftime("%A")
date_name = today.strftime("%Y-%m-%d")


# ==========================================
# CONTENT TYPE
# ==========================================

if day_name == "Sunday":

    content_type = "10-Minute YouTube Long Video"

    prompt = """
You are the content creation AI for the YouTube channel "Vexora Tales".

Audience: USA
Language: Natural American English
Format: Faceless YouTube video
Length: Approximately 10 minutes
Niche: Original viral stories and animated explainers.

Create a completely ORIGINAL story.

Do not copy existing YouTube videos.
Do not use copyrighted movie or TV characters.
Do not use copyrighted clips.
Do not make false claims.
Do not create repetitive spam.

The first 10 seconds must have a powerful hook.

Maintain curiosity throughout the video.

Every scene must be easy to animate.

Create a satisfying ending.

OUTPUT:

TITLE:
One clickable but honest title.

HOOK:
Opening narration for approximately 10 seconds.

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

SCENE 5:
VISUAL:
VOICEOVER:

SCENE 6:
VISUAL:
VOICEOVER:

SCENE 7:
VISUAL:
VOICEOVER:

SCENE 8:
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

Audience: USA
Language: Natural American English
Format: Faceless YouTube Short
Length: Approximately 30 seconds
Niche: Original viral stories and animated explainers.

Create a completely ORIGINAL story.

Do not copy existing YouTube videos.
Do not use copyrighted movie or TV characters.
Do not use copyrighted clips.
Do not make false claims.
Do not create repetitive spam.

The first 1–2 seconds must immediately create curiosity.

Keep the story fast and easy to understand.

Create a strong twist, reveal or payoff.

Every scene must be easy to animate.

OUTPUT:

TITLE:
One clickable but honest title.

HOOK:
Opening hook.

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


# ==========================================
# GENERATE STORY
# ==========================================

print("=" * 50)
print("VEXORA TALES AI")
print("=" * 50)
print(f"Date: {date_name}")
print(f"Day: {day_name}")
print(f"Content Type: {content_type}")
print("")
print("Generating story...")

response = retry_call(
    lambda: client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt
    )
)

story = response.text.strip()

if not story:
    raise RuntimeError("Gemini ne story generate nahi ki.")

print("STORY GENERATED: YES")


# ==========================================
# SAVE STORY
# ==========================================

with open("story.txt", "w", encoding="utf-8") as file:
    file.write(story)


# ==========================================
# EXTRACT NARRATION
# ==========================================

print("Preparing narration...")

voice_prompt = f"""
You are preparing narration for a professional American YouTube video.

Read the script below.

Extract ONLY the words that should be spoken by the narrator.

Include:
- Hook narration
- Every scene voiceover
- Ending narration
- Call to action narration

Remove:
- VISUAL descriptions
- Scene headings
- Labels
- Instructions
- Metadata

Do not add new story information.

Use natural American English.

SCRIPT:

{story}
"""

voice_response = retry_call(
    lambda: client.models.generate_content(
        model=TEXT_MODEL,
        contents=voice_prompt
    )
)

narration = voice_response.text.strip()

if not narration:
    raise RuntimeError("Narration generate nahi hua.")

with open("narration.txt", "w", encoding="utf-8") as file:
    file.write(narration)

print("NARRATION GENERATED: YES")


# ==========================================
# GEMINI AI VOICE
# ==========================================

print("Generating AI voice...")

tts_prompt = f"""
Read the following narration as a professional American YouTube storyteller.

Voice style:
- Male storyteller
- Natural American English
- Clear pronunciation
- Cinematic
- Suspenseful
- Confident
- Medium-fast pacing
- Natural emotion
- Professional YouTube narration

Do not add any words.

NARRATION:

{narration}
"""

tts_response = retry_call(
    lambda: client.interactions.create(
        model=TTS_MODEL,
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
)


# ==========================================
# SAVE WAV
# ==========================================

if not tts_response.output_audio:
    raise RuntimeError("Gemini TTS ne audio return nahi kiya.")

audio_data = base64.b64decode(
    tts_response.output_audio.data
)

with wave.open("voice.wav", "wb") as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(24000)
    wav_file.writeframes(audio_data)

print("AI VOICE GENERATED: YES")


# ==========================================
# FINAL STATUS
# ==========================================

print("")
print("FILES CREATED:")
print("- story.txt")
print("- narration.txt")
print("- voice.wav")

print("")
print("PIPELINE STATUS: SUCCESS")
print("=" * 50)
