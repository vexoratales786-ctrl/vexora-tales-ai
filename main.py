import os
import base64
import time
import wave
import subprocess
import json
import re
from datetime import datetime, timedelta
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

TEXT_MODEL = os.getenv("TEXT_MODEL", "gemini-3.1-flash-lite")
TTS_MODEL = os.getenv("TTS_MODEL", "gemini-3.1-flash-tts-preview")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")


# ============================================================
# GEMINI START
# ============================================================

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY secret nahi mila.")

client = genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# SELF RECOVERY
# ============================================================

def retry_call(function, max_attempts=4):

    last_error = None

    for attempt in range(1, max_attempts + 1):

        try:
            return function()

        except Exception as error:

            last_error = error

            print(
                f"Request failed "
                f"(attempt {attempt}/{max_attempts}): {error}"
            )

            if attempt < max_attempts:

                wait_time = min(60, 2 ** attempt)

                print(
                    f"Self-recovery: waiting "
                    f"{wait_time} seconds..."
                )

                time.sleep(wait_time)

    raise last_error


# ============================================================
# METADATA PARSER
# ============================================================

def parse_metadata(text):

    title_match = re.search(
        r"(?im)^TITLE:\s*(.+)$",
        text
    )

    desc_match = re.search(
        r"(?im)^DESCRIPTION:\s*(.*?)(?=^TAGS:|\Z)",
        text,
        re.S
    )

    tags_match = re.search(
        r"(?im)^TAGS:\s*(.+)$",
        text
    )

    title = (
        title_match.group(1).strip()
        if title_match
        else "Vexora Tales Original Story"
    )

    description = (
        desc_match.group(1).strip()
        if desc_match
        else "An original story created by Vexora Tales."
    )

    tags_raw = (
        tags_match.group(1).strip()
        if tags_match
        else "Vexora Tales, storytelling, mystery"
    )

    tags = [
        x.strip().lstrip("#")
        for x in tags_raw.split(",")
        if x.strip()
    ]

    title = title[:95]

    description = description[:4900]

    clean_tags = []

    total = 0

    for tag in tags[:15]:

        extra = len(tag) + (
            1 if clean_tags else 0
        )

        if total + extra > 450:
            break

        clean_tags.append(tag)

        total += extra

    return title, description, clean_tags


# ============================================================
# YOUTUBE AUTHENTICATION
# ============================================================

def build_youtube_services():

    if not (
        YOUTUBE_CLIENT_ID
        and YOUTUBE_REFRESH_TOKEN
        and YOUTUBE_CLIENT_SECRET
    ):

        print(
            "WARNING: YouTube secrets missing; "
            "upload/analytics skipped."
        )

        return None, None

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

    analytics = build(
        "youtubeAnalytics",
        "v2",
        credentials=credentials
    )

    print("YOUTUBE AUTHENTICATION READY.")

    return youtube, analytics


# ============================================================
# PREVIOUS CHANNEL ANALYTICS
# ============================================================

def get_recent_analytics(analytics):

    if analytics is None:
        return "No previous analytics available."

    today = datetime.now(
        ZoneInfo(TIMEZONE)
    ).date()

    end_date = today - timedelta(days=1)

    start_date = end_date - timedelta(days=7)

    try:

        response = analytics.reports().query(

            ids="channel==MINE",

            startDate=start_date.isoformat(),

            endDate=end_date.isoformat(),

            metrics=(
                "views,"
                "likes,"
                "comments,"
                "estimatedMinutesWatched,"
                "averageViewDuration,"
                "averageViewPercentage,"
                "subscribersGained"
            ),

            dimensions="video",

            sort="-views",

            maxResults=10

        ).execute()

        rows = response.get(
            "rows",
            []
        )

        if not rows:

            return "No usable analytics yet."

        headers = [
            h["name"]
            for h in response.get(
                "columnHeaders",
                []
            )
        ]

        summary = []

        for row in rows:

            item = dict(
                zip(
                    headers,
                    row
                )
            )

            summary.append(item)

        with open(
            "analytics_feedback.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                summary,
                f,
                indent=2
            )

        return json.dumps(
            summary,
            indent=2
        )

    except Exception as error:

        print(
            "Analytics unavailable:",
            error
        )

        return (
            "Analytics unavailable "
            "for this run."
        )


# ============================================================
# LIVE YOUTUBE TREND SIGNALS
# ============================================================

def get_trend_signals(youtube):

    if youtube is None:

        return (
            "No live YouTube trend signals "
            "available."
        )

    queries = [

        "mystery strange events",

        "science technology mystery",

        "American history strange facts"

    ]

    candidates = []

    for query in queries:

        try:

            response = youtube.search().list(

                part="snippet",

                q=query,

                type="video",

                regionCode="US",

                relevanceLanguage="en",

                order="date",

                publishedAfter=(
                    datetime.now(
                        ZoneInfo("UTC")
                    )
                    - timedelta(days=3)
                ).isoformat().replace(
                    "+00:00",
                    "Z"
                ),

                maxResults=5

            ).execute()

            for item in response.get(
                "items",
                []
            ):

                candidates.append({

                    "id": item["id"].get(
                        "videoId"
                    ),

                    "title": item["snippet"].get(
                        "title",
                        ""
                    ),

                    "publishedAt": item[
                        "snippet"
                    ].get(
                        "publishedAt",
                        ""
                    ),

                    "channelTitle": item[
                        "snippet"
                    ].get(
                        "channelTitle",
                        ""
                    )

                })

        except Exception as error:

            print(
                f"Trend search failed for "
                f"'{query}': {error}"
            )

    ids = [
        x["id"]
        for x in candidates
        if x.get("id")
    ]

    if not ids:

        return (
            "No live trend signals "
            "available."
        )

    try:

        stats_response = youtube.videos().list(

            part="snippet,statistics",

            id=",".join(
                dict.fromkeys(ids)
            )[:8000]

        ).execute()

        now_utc = datetime.now(
            ZoneInfo("UTC")
        )

        for item in stats_response.get(
            "items",
            []
        ):

            vid = item["id"]

            stat = item.get(
                "statistics",
                {}
            )

            views = int(
                stat.get(
                    "viewCount",
                    0
                )
            )

            pub = item.get(
                "snippet",
                {}
            ).get(
                "publishedAt",
                ""
            )

            try:

                published = datetime.fromisoformat(
                    pub.replace(
                        "Z",
                        "+00:00"
                    )
                )

                hours = max(
                    (
                        now_utc - published
                    ).total_seconds()
                    / 3600,
                    1
                )

            except Exception:

                hours = 72

            for candidate in candidates:

                if candidate["id"] == vid:

                    candidate[
                        "views"
                    ] = views

                    candidate[
                        "views_per_hour"
                    ] = round(
                        views / hours,
                        1
                    )

                    break

    except Exception as error:

        print(
            "Trend statistics unavailable:",
            error
        )

    candidates.sort(
        key=lambda x:
            x.get(
                "views_per_hour",
                0
            ),
        reverse=True
    )

    top = candidates[:12]

    with open(
        "trend_signals.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            top,
            f,
            indent=2
        )

    return json.dumps(
        top,
        indent=2
    )


# ============================================================
# START SERVICES
# ============================================================

youtube, youtube_analytics = (
    build_youtube_services()
)


# ============================================================
# DATE / CONTENT TYPE
# ============================================================

now = datetime.now(
    ZoneInfo(TIMEZONE)
)

day_name = now.strftime(
    "%A"
)

date_name = now.strftime(
    "%Y-%m-%d"
)

if day_name == "Sunday":

    content_type = (
        "10-Minute YouTube Long Video"
    )

else:

    content_type = (
        "30-Second YouTube Short"
    )


print("=" * 60)

print(
    "VEXORA TALES AI AUTONOMOUS AGENT"
)

print(
    "Date:",
    date_name
)

print(
    "Day:",
    day_name
)

print(
    "Content:",
    content_type
)

print("=" * 60)


# ============================================================
# TREND + PERFORMANCE RESEARCH
# ============================================================

trend_signals = get_trend_signals(
    youtube
)

performance_feedback = (
    get_recent_analytics(
        youtube_analytics
    )
)


# ============================================================
# AI TOPIC SELECTION
# ============================================================

trend_prompt = f"""

You are the senior content strategist
for a USA-focused faceless YouTube channel.

Channel:
{CHANNEL_NAME}

Audience:
American English-speaking viewers.

Today's date:
{date_name}

Content type:
{content_type}

LIVE YOUTUBE TREND SIGNALS:

{trend_signals}

RECENT CHANNEL PERFORMANCE:

{performance_feedback}

Choose ONE ORIGINAL topic with strong potential.

Use the live signals and performance
feedback as inputs.

Do NOT copy any creator.

Do NOT copy scripts.

Do NOT use copyrighted clips.

Preferred areas:

- mystery
- strange real events
- science
- technology
- space
- human behavior
- unexplained events
- shocking facts
- interesting American stories

If previous videos performed poorly,
learn from the metrics.

Weak views:
Improve topic specificity and hook.

Low average view duration:
Improve pacing and curiosity.

Low average view percentage:
Make the story tighter.

Low likes/comments:
Improve emotional payoff.

Do NOT claim guaranteed virality.

Return ONLY:

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


trend_text = (
    trend_response.text.strip()
)


print(
    "\nSELECTED TREND:"
)

print(
    trend_text
)


# ============================================================
# ORIGINAL SCRIPT
# ============================================================

if content_type == (
    "30-Second YouTube Short"
):

    script_prompt = f"""

Create an ORIGINAL
30-second YouTube Short
for {CHANNEL_NAME}.

Audience:
USA.

Language:
American English.

Selected topic:

{trend_text}

Requirements:

- extremely strong first 2 seconds
- fast pacing
- curiosity gap
- original wording
- simple storytelling
- clear visual storytelling
- no copied script
- no copyrighted clips
- satisfying ending
- encourage replay
- approximately 65-85 spoken words

Return ONLY the narrator script.

"""

else:

    script_prompt = f"""

Create an ORIGINAL approximately
10-minute YouTube video
for {CHANNEL_NAME}.

Audience:
USA.

Language:
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


script = (
    script_response.text.strip()
)


if not script:

    raise RuntimeError(
        "Script generate nahi hua."
    )


with open(
    "script.txt",
    "w",
    encoding="utf-8"
) as f:

    f.write(script)


print(
    "ORIGINAL SCRIPT GENERATED."
)


# ============================================================
# TITLE / DESCRIPTION / TAGS
# ============================================================

metadata_prompt = f"""

Create YouTube metadata
for this original video.

Channel:
{CHANNEL_NAME}

Audience:
USA.

Content type:
{content_type}

SCRIPT:

{script}

Return exactly:

TITLE:
DESCRIPTION:
TAGS:

Title should be
curiosity-driven but NOT misleading.

Description should be natural.

Tags should be comma-separated.

"""


metadata_response = retry_call(

    lambda: client.models.generate_content(

        model=TEXT_MODEL,

        contents=metadata_prompt

    )
)


metadata = (
    metadata_response.text.strip()
)


with open(
    "metadata.txt",
    "w",
    encoding="utf-8"
) as f:

    f.write(metadata)


title, description, tags = (
    parse_metadata(metadata)
)


if (
    content_type
    == "30-Second YouTube Short"
):

    if "#shorts" not in title.lower():

        title = (
            f"{title} #Shorts"
        )


print(
    "TITLE + DESCRIPTION + TAGS GENERATED."
)


# ============================================================
# AI VOICE
# ============================================================

tts_prompt = f"""

Read the following script
as a professional American
YouTube narrator.

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

        response_format={
            "type": "audio"
        },

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


with wave.open(
    "voice.wav",
    "wb"
) as wav:

    wav.setnchannels(1)

    wav.setsampwidth(2)

    wav.setframerate(24000)

    wav.writeframes(audio_data)


print(
    "AI VOICE GENERATED."
)


# ============================================================
# VIDEO CREATION
# ============================================================

if content_type == (
    "30-Second YouTube Short"
):

    video_filter = (

        "color=c=black:"
        "s=1080x1920:"
        "r=30,"

        "drawtext="
        "text='VEXORA TALES':"
        "fontcolor=white:"
        "fontsize=70:"
        "x=(w-text_w)/2:"
        "y=h/2"

    )

else:

    video_filter = (

        "color=c=black:"
        "s=1920x1080:"
        "r=30,"

        "drawtext="
        "text='VEXORA TALES':"
        "fontcolor=white:"
        "fontsize=90:"
        "x=(w-text_w)/2:"
        "y=h/2"

    )


video_command = [

    "ffmpeg",

    "-y",

    "-f",
    "lavfi",

    "-i",
    video_filter,

    "-i",
    "voice.wav",

    "-shortest",

    "-c:v",
    "libx264",

    "-preset",
    "veryfast",

    "-pix_fmt",
    "yuv420p",

    "-c:a",
    "aac",

    "-b:a",
    "128k",

    "video.mp4"

]


subprocess.run(
    video_command,
    check=True
)


print(
    "VIDEO CREATED."
)


# ============================================================
# THUMBNAIL
# ============================================================

thumbnail_command = [

    "ffmpeg",

    "-y",

    "-i",
    "video.mp4",

    "-frames:v",
    "1",

    "-vf",
    "scale=1280:720",

    "thumbnail.jpg"

]


subprocess.run(
    thumbnail_command,
    check=True
)


print(
    "THUMBNAIL CREATED."
)


# ============================================================
# YOUTUBE UPLOAD
# ============================================================

def upload_to_youtube():

    if youtube is None:

        raise RuntimeError(
            "YouTube authentication "
            "is not available."
        )


    body = {

        "snippet": {

            "title": title,

            "description": description,

            "tags": tags,

            "categoryId": "24",

            "defaultLanguage": "en",

            "defaultAudioLanguage": "en"

        },

        "status": {

            "privacyStatus": "public",

            "selfDeclaredMadeForKids": False

        }

    }


    print(
        "STARTING YOUTUBE UPLOAD..."
    )


    insert_request = (
        youtube.videos().insert(

            part="snippet,status",

            body=body,

            media_body=MediaFileUpload(

                "video.mp4",

                mimetype="video/mp4",

                chunksize=8 * 1024 * 1024,

                resumable=True

            )

        )
    )


    response = None


    while response is None:

        status, response = (
            insert_request.next_chunk()
        )

        if status:

            print(
                "UPLOAD PROGRESS:",
                int(
                    status.progress()
                    * 100
                ),
                "%"
            )


    video_id = response["id"]


    video_url = (
        f"https://www.youtube.com/watch?v="
        f"{video_id}"
    )


    print(
        "VIDEO UPLOADED:",
        video_url
    )


    # ========================================================
    # THUMBNAIL UPLOAD
    # ========================================================

    try:

        youtube.thumbnails().set(

            videoId=video_id,

            media_body=MediaFileUpload(

                "thumbnail.jpg",

                mimetype="image/jpeg"

            )

        ).execute()


        print(
            "THUMBNAIL UPLOADED."
        )

    except Exception as error:

        print(
            "Thumbnail upload failed:",
            error
        )


    # ========================================================
    # SAVE UPLOAD RESULT
    # ========================================================

    with open(
        "upload_result.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(

            {

                "video_id":
                    video_id,

                "url":
                    video_url,

                "title":
                    title,

                "content_type":
                    content_type,

                "uploaded_at":
                    datetime.now(
                        ZoneInfo(
                            TIMEZONE
                        )
                    ).isoformat()

            },

            f,

            indent=2

        )


    return (
        video_id,
        video_url
    )


# ============================================================
# RUN YOUTUBE UPLOAD
# ============================================================

if youtube is not None:

    video_id, video_url = retry_call(

        upload_to_youtube,

        max_attempts=3

    )


    print("=" * 60)

    print(
        "YOUTUBE UPLOAD COMPLETE"
    )

    print(
        "VIDEO URL:",
        video_url
    )

    print("=" * 60)

else:

    print(
        "UPLOAD SKIPPED: "
        "YouTube authentication unavailable."
    )


# ============================================================
# COMPLETE
# ============================================================

print(
    "VEXORA TALES AI RUN COMPLETE."
)
