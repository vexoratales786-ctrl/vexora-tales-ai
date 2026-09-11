import os
import json
import base64
import time
import wave
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai


# ============================================================
# VEXORA TALES AI - AUTONOMOUS YOUTUBE AGENT
# ============================================================

CHANNEL_NAME = "Vexora Tales"
TARGET_AUDIENCE = "USA"
TIMEZONE = "Asia/Kolkata"

TEXT_MODEL = os.getenv("TEXT_MODEL", "gemini-3.7-flash")
TTS_MODEL = os.getenv("TTS_MODEL", "gemini-3.1-flash-tts-preview")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY secret nahi mila.")

client = genai.Client(api_key=api_key)


# ============================================================
# RETRY / SELF-RECOVERY
# ============================================================

def retry_call(function, max_attempts=6):
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return function()

        except Exception as error:
            last_error = error
            print(
                f"AI request failed "
                f"(attempt {attempt}/{max_attempts}): {error}"
            )

            if attempt < max_attempts:
                wait_time = min(60, 2 ** attempt)
                print(f"Self-recovery: waiting {wait_time} seconds...")
                time.sleep(wait_time)

    raise last_error


# ============================================================
# DATE / CONTENT TYPE
# ============================================================

now = datetime.now(ZoneInfo(TIMEZONE))
day_name = now.strftime("%A")
date_name = now.strftime("%Y-%m-%d")

if day_name == "Sunday":
    content_type = "10-Minute YouTube Long Video"
else:
    content_type = "30-Second YouTube Short"

print("========================================")
print("VEXORA TALES AI AGENT")
print("Date:", date_name)
print("Day:", day_name)
print("Content:", content_type)
print("========================================")


# ============================================================
# TREND + TOPIC RESEARCH
# ============================================================

trend_prompt = f"""
You are the strategy brain of a USA-focused faceless YouTube channel
called "{CHANNEL_NAME}".

Today: {date_name}
Content type: {content_type}

Choose a HIGH-POTENTIAL topic for an original video.

Focus on:
- USA audience
- English language
- Faceless format
- Strong curiosity
- Strong first 3-second hook
- Shareability
- Current-interest style topics
- Stories, mysteries, science, history, technology,
  strange events, discoveries and animated explainers
- Avoid saturated generic AI spam
- Never copy another creator's script
- Never recommend copyrighted clips as the main content

Return ONLY valid JSON:

{{
  "topic": "topic",
  "angle": "unique angle",
  "hook": "opening hook",
  "title": "suggested title",
  "reason": "why this topic has potential"
}}
"""

trend_response = retry_call(
    lambda: client.models.generate_content(
        model=TEXT_MODEL,
        contents=trend_prompt
    )
)

raw_trend = trend_response.text.strip()

try:
    trend = json.loads(raw_trend)
except Exception:
    trend = {
        "topic": "A strange unexplained event that sounds impossible",
        "angle": "Tell the story through a surprising investigation",
        "hook": "This sounds impossible, but the evidence tells a different story.",
        "title": "The Strange Story Nobody Can Explain",
        "reason": "Strong curiosity and mystery angle"
    }

print("Selected topic:", trend["topic"])


# ============================================================
# ORIGINAL SCRIPT
# ============================================================

if content_type == "30-Second YouTube Short":

    script_prompt = f"""
Create a completely ORIGINAL YouTube Short for "{CHANNEL_NAME}".

Audience: USA
Language: Natural American English
Length: approximately 30 seconds
Format: faceless
Topic: {trend["topic"]}
Angle: {trend["angle"]}
Hook: {trend["hook"]}

Rules:
- Original writing only.
- Do not copy existing videos.
- No copyrighted movie/show dialogue.
- No reused clips.
- Very strong first 2-3 seconds.
- Fast pacing.
- Interesting ending.
- Include narration only.
- Do not include scene directions.
- Do not include labels.
"""

else:

    script_prompt = f"""
Create a completely ORIGINAL approximately 10-minute YouTube
faceless documentary/story video for "{CHANNEL_NAME}".

Audience: USA
Language: Natural American English
Topic: {trend["topic"]}
Angle: {trend["angle"]}

Rules:
- Original writing only.
- No copied scripts.
- No copyrighted dialogue.
- Strong opening hook.
- Clear story structure.
- Maintain curiosity throughout.
- Include useful facts and explanations where appropriate.
- Strong ending.
- Write narration only.
- Do not include scene directions.
- Do not include labels.
"""

script_response = retry_call(
    lambda: client.models.generate_content(
        model=TEXT_MODEL,
        contents=script_prompt
    )
)

script = script_response.text.strip()

if not script:
    raise RuntimeError("Script generate nahi hua.")

with open("story.txt", "w", encoding="utf-8") as file:
    file.write(script)

print("Original script generated.")


# ============================================================
# TITLE / DESCRIPTION
# ============================================================

metadata_prompt = f"""
Create YouTube metadata for this ORIGINAL video.

Channel: {CHANNEL_NAME}
Audience: USA

Script:
{script}

Return ONLY valid JSON:

{{
  "title": "high CTR but honest title",
  "description": "YouTube description",
  "hashtags": ["#shorts", "#mystery", "#story"]
}}
"""

metadata_response = retry_call(
    lambda: client.models.generate_content(
        model=TEXT_MODEL,
        contents=metadata_prompt
    )
)

try:
    metadata = json.loads(metadata_response.text.strip())
except Exception:
    metadata = {
        "title": trend["title"],
        "description": f"An original story from {CHANNEL_NAME}.",
        "hashtags": ["#shorts", "#story"]
    }

with open("metadata.json", "w", encoding="utf-8") as file:
    json.dump(metadata, file, indent=2)


# ============================================================
# AI NARRATION
# ============================================================

tts_prompt = f"""
Read the following narration as a professional American YouTube
storyteller.

Natural, engaging, clear voice.
Good pacing.
Build suspense where appropriate.
Do not add words.

Narration:
{script}
"""

tts_response = retry_call(
    lambda: client.interactions.create(
        model=TTS_MODEL,
        input=tts_prompt,
        response_format={"type": "audio"},
        generation_config={
            "speech_config": [
                {"voice": "Kore"}
            ]
        }
    )
)

audio_data = base64.b64decode(tts_response.output_audio.data)

with wave.open("voice.wav", "wb") as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(24000)
    wav_file.writeframes(audio_data)

print("AI voice generated.")


# ============================================================
# VIDEO CREATION
# ============================================================

video_title = metadata["title"].replace("'", "")

ffmpeg_command = [
    "ffmpeg",
    "-y",
    "-f", "lavfi",
    "-i", "color=c=black:s=1080x1920:r=30",
    "-i", "voice.wav",
    "-t", "30" if content_type.startswith("30") else "600",
    "-vf",
    (
        "drawtext="
        "fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        f"text='{video_title[:80]}':"
        "fontcolor=white:"
        "fontsize=58:"
        "x=(w-text_w)/2:"
        "y=(h-text_h)/2:"
        "box=1:"
        "boxborderw=30:"
        "boxcolor=black@0.75"
    ),
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-shortest",
    "vexora_video.mp4"
]

try:
    subprocess.run(
        ffmpeg_command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
except Exception as error:
    raise RuntimeError(f"Video creation failed: {error}")

print("Video created.")


# ============================================================
# THUMBNAIL
# ============================================================

thumbnail_command = [
    "ffmpeg",
    "-y",
    "-i", "vexora_video.mp4",
    "-frames:v", "1",
    "-vf", "scale=1280:720",
    "thumbnail.jpg"
]

subprocess.run(
    thumbnail_command,
    check=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

print("Thumbnail created.")


# ============================================================
# SAVE FINAL STATUS
# ============================================================

status = {
    "channel": CHANNEL_NAME,
    "date": date_name,
    "content_type": content_type,
    "topic": trend["topic"],
    "title": metadata["title"],
    "video": "vexora_video.mp4",
    "thumbnail": "thumbnail.jpg",
    "status": "VIDEO_READY",
    "upload": "PENDING_YOUTUBE_CONNECTION"
}

with open("agent_status.json", "w", encoding="utf-8") as file:
    json.dump(status, file, indent=2)

print("========================================")
print("PIPELINE STATUS: SUCCESS")
print("Video + voice + thumbnail ready.")
print("========================================")
