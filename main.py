import os
import base64
import time
import wave
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# ============================================================
# VEXORA TALES AI - AUTONOMOUS YOUTUBE AGENT
# ============================================================

CHANNEL_NAME = "Vexora Tales"
TARGET_AUDIENCE = "USA"
TIMEZONE = "Asia/Kolkata"

TEXT_MODEL = os.getenv("TEXT_MODEL", "gemini-3.7-flash")
TTS_MODEL = os.getenv("TTS_MODEL", "gemini-3.1-flash-tts-preview")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")


if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY secret nahi mila.")

client = genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# SELF RECOVERY
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


print("=" * 60)
print("VEXORA TALES AI AUTONOMOUS AGENT")
print("Date:", date_name)
print("Day:", day_name)
print("Content:", content_type)
print("=" * 60)


# ============================================================
# TREND-AWARE TOPIC SELECTION
# ============================================================

trend_prompt = f"""
You are the content strategist for a USA-focused faceless YouTube channel.

Channel:
{CHANNEL_NAME}

Target audience:
American English-speaking viewers.

Today's date:
{date_name}

Content type:
{content_type}

Choose ONE high-potential ORIGINAL topic.

The topic should:
- have strong curiosity
- work for a faceless channel
- be understandable to a USA audience
- have viral potential
- NOT copy another creator's script
- NOT reuse copyrighted video
- be suitable for original AI-generated storytelling
- have a strong hook
- have potential for high retention

Preferred areas:
mystery, history, strange real events, science, technology,
space, human behavior, unexplained events, shocking facts,
interesting American stories.

Do NOT claim that the topic is guaranteed viral.

Return ONLY this format:

TOPIC: ...
ANGLE: ...
HOOK: ...
REASON: ...
"""

trend_response = retry_call(
    lambda: client.models.generate_content(
        model=TEXT_MODEL,
        contents=trend_prompt
    )
)

trend_text = trend_response.text.strip()

print("\nSELECTED TREND:")
print(trend_text)


# ============================================================
# ORIGINAL SCRIPT
# ============================================================

if content_type == "30-Second YouTube Short":

    script_prompt = f"""
Create an ORIGINAL 30-second YouTube Short for {CHANNEL_NAME}.

USA audience.
American English.

Selected topic:
{trend_text}

Requirements:
- extremely strong first 2 seconds
- fast pacing
- curiosity gap
- simple storytelling
- original wording
- no copied script
- no copyrighted clips
- ending should encourage viewers to watch again
- approximately 65-85 spoken words

Return ONLY the narrator script.
"""

else:

    script_prompt = f"""
Create an ORIGINAL approximately 10-minute YouTube video
for {CHANNEL_NAME}.

USA audience.
American English.

Selected topic:
{trend_text}

Requirements:
- strong opening hook
- documentary/storytelling style
- original wording
- detailed story
- frequent curiosity points
- strong retention
- natural transitions
- satisfying ending
- approximately 1300-1600 spoken words
- no copied script
- no copyrighted clips

Return ONLY the narrator script.
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

with open("script.txt", "w", encoding="utf-8") as f:
    f.write(script)

print("\nORIGINAL SCRIPT GENERATED.")


# ============================================================
# TITLE / DESCRIPTION / TAGS
# ============================================================

metadata_prompt = f"""
Create YouTube metadata for this original video.

Channel: {CHANNEL_NAME}
Audience: USA
Content type: {content_type}

SCRIPT:
{script}

Return exactly:

TITLE:
DESCRIPTION:
TAGS:

Title should be curiosity-driven but NOT misleading.
Description should be natural.
Tags should be comma-separated.
"""

metadata_response = retry_call(
    lambda: client.models.generate_content(
        model=TEXT_MODEL,
        contents=metadata_prompt
    )
)

metadata = metadata_response.text.strip()

with open("metadata.txt", "w", encoding="utf-8") as f:
    f.write(metadata)

print("TITLE + DESCRIPTION + TAGS GENERATED.")


# ============================================================
# AI VOICE
# ============================================================

tts_prompt = f"""
Read the following script as a professional American YouTube narrator.

Voice:
- natural
- confident
- cinematic
- clear
- engaging
- appropriate for USA audience
- no extra words
- do not change the script

SCRIPT:

{script}
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

audio_data = base64.b64decode(
    tts_response.output_audio.data
)

with wave.open("voice.wav", "wb") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(24000)
    wav.writeframes(audio_data)

print("AI VOICE GENERATED.")


# ============================================================
# VIDEO CREATION
# ============================================================

# Create a simple cinematic background using FFmpeg.
# This keeps the system fully automatic and avoids copyrighted footage.

video_filter = (
    "color=c=black:s=1080x1920:r=30,"
    "drawtext=text='VEXORA TALES':"
    "fontcolor=white:"
    "fontsize=70:"
    "x=(w-text_w)/2:"
    "y=h/2"
)

if content_type == "30-Second YouTube Short":

    video_command = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", video_filter,
        "-i", "voice.wav",
        "-shortest",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "video.mp4"
    ]

else:

    video_filter_long = (
        "color=c=black:s=1920x1080:r=30,"
        "drawtext=text='VEXORA TALES':"
        "fontcolor=white:"
        "fontsize=90:"
        "x=(w-text_w)/2:"
        "y=h/2"
    )

    video_command = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", video_filter_long,
        "-i", "voice.wav",
        "-shortest",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "video.mp4"
    ]


subprocess.run(video_command, check=True)

print("VIDEO CREATED.")


# ============================================================
# THUMBNAIL
# ============================================================

thumbnail_command = [
    "ffmpeg",
    "-y",
    "-i", "video.mp4",
    "-frames:v", "1",
    "-vf", "scale=1280:720",
    "thumbnail.jpg"
]

subprocess.run(thumbnail_command, check=True)

print("THUMBNAIL CREATED.")


# ============================================================
# YOUTUBE AUTHENTICATION
# ============================================================

youtube = None

if (
    YOUTUBE_CLIENT_ID
    and YOUTUBE_REFRESH_TOKEN
    and YOUTUBE_CLIENT_SECRET
):

    credentials = Credentials(
        token=None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/yt-analytics.readonly"
        ]
    )

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials
    )

    print("YOUTUBE AUTHENTICATION READY.")

else:

    print(
        "WARNING: YouTube Client Secret abhi GitHub secret "
        "mein available nahi hai."
    )


# ============================================================
# METADATA PARSER
# ============================================================

title = "Vexora Tales Original Story"

description = (
    "An original story created by
