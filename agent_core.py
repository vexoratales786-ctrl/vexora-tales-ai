# Vexora Tales AI core is intentionally kept in one module.
# The web app imports these functions to provide a chat-style control layer.

import os
import base64
import json
import re
import subprocess
import tempfile
import wave
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from google import genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
ASSETS = DATA / "assets"
ASSETS.mkdir(exist_ok=True)
TZ = ZoneInfo(os.getenv("TIMEZONE", "Asia/Kolkata"))
CHANNEL_NAME = "Vexora Tales"
TEXT_MODEL = os.getenv("TEXT_MODEL", "gemini-3.1-flash-lite")
TTS_MODEL = os.getenv("TTS_MODEL", "gemini-3.1-flash-tts-preview")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gemini-3.1-flash-image")


def _client():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is missing")
    return genai.Client(api_key=key)


def _save_json(name, value):
    (DATA / name).write_text(json.dumps(value, indent=2), encoding="utf-8")


def _load_json(name, default=None):
    p = DATA / name
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def youtube_services():
    cid = os.getenv("YOUTUBE_CLIENT_ID")
    secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh = os.getenv("YOUTUBE_REFRESH_TOKEN")
    if not (cid and secret and refresh):
        return None, None
    creds = Credentials(
        token=None,
        refresh_token=refresh,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=cid,
        client_secret=secret,
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/yt-analytics.readonly",
        ],
    )
    return build("youtube", "v3", credentials=creds), build("youtubeAnalytics", "v2", credentials=creds)


def recent_analytics(days=7):
    _, analytics = youtube_services()
    if not analytics:
        return {"available": False, "message": "YouTube Analytics credentials unavailable."}
    end = datetime.now(TZ).date() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    try:
        r = analytics.reports().query(
            ids="channel==MINE", startDate=start.isoformat(), endDate=end.isoformat(),
            metrics="views,likes,comments,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained",
            dimensions="video", sort="-views", maxResults=20,
        ).execute()
        headers = [x["name"] for x in r.get("columnHeaders", [])]
        rows = [dict(zip(headers, row)) for row in r.get("rows", [])]
        result = {"available": True, "start": start.isoformat(), "end": end.isoformat(), "rows": rows}
        _save_json("analytics.json", result)
        return result
    except Exception as e:
        return {"available": False, "message": str(e)}


def channel_status():
    youtube, _ = youtube_services()
    if not youtube:
        return {"connected": False, "message": "YouTube is not connected."}
    try:
        ch_items = youtube.channels().list(part="snippet,statistics,contentDetails", mine=True).execute().get("items", [])
        if not ch_items:
            return {"connected": False, "message": "No YouTube channel found for this account."}
        ch = ch_items[0]
        stats = ch.get("statistics", {})
        uploads = ch.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
        videos = []
        if uploads:
            pl = youtube.playlistItems().list(part="snippet,contentDetails", playlistId=uploads, maxResults=10).execute()
            ids = [x["contentDetails"]["videoId"] for x in pl.get("items", [])]
            if ids:
                vr = youtube.videos().list(part="snippet,statistics,status", id=",".join(ids)).execute()
                videos = vr.get("items", [])
        result = {
            "connected": True, "channel": ch.get("snippet", {}).get("title", CHANNEL_NAME),
            "subscribers": stats.get("subscriberCount", "0"), "views": stats.get("viewCount", "0"),
            "video_count": stats.get("videoCount", "0"),
            "recent_videos": [{
                "id": v["id"], "title": v.get("snippet", {}).get("title", ""),
                "views": v.get("statistics", {}).get("viewCount", "0"),
                "likes": v.get("statistics", {}).get("likeCount", "0"),
                "comments": v.get("statistics", {}).get("commentCount", "0"),
                "publishedAt": v.get("snippet", {}).get("publishedAt", ""),
                "privacy": v.get("status", {}).get("privacyStatus", ""),
            } for v in videos],
        }
        _save_json("channel_status.json", result)
        return result
    except Exception as e:
        return {"connected": False, "message": str(e)}


def trend_research():
    youtube, _ = youtube_services()
    if not youtube:
        return []
    queries = ["mystery strange events", "science technology", "space discoveries", "American history strange facts", "human behavior mystery"]
    candidates = []
    cutoff = (datetime.now(ZoneInfo("UTC")) - timedelta(days=3)).isoformat().replace("+00:00", "Z")
    for q in queries:
        try:
            r = youtube.search().list(part="snippet", q=q, type="video", regionCode="US", relevanceLanguage="en", order="date", publishedAfter=cutoff, maxResults=5).execute()
            for x in r.get("items", []):
                vid = x.get("id", {}).get("videoId")
                if vid:
                    candidates.append({"id": vid, "title": x["snippet"].get("title", ""), "channel": x["snippet"].get("channelTitle", ""), "publishedAt": x["snippet"].get("publishedAt", "")})
        except Exception:
            pass
    ids = list(dict.fromkeys(x["id"] for x in candidates))
    if ids:
        try:
            stats = youtube.videos().list(part="snippet,statistics", id=",".join(ids)).execute()
            lookup = {x["id"]: x for x in stats.get("items", [])}
            now = datetime.now(ZoneInfo("UTC"))
            for c in candidates:
                x = lookup.get(c["id"], {})
                views = int(x.get("statistics", {}).get("viewCount", 0))
                try:
                    published = datetime.fromisoformat(c["publishedAt"].replace("Z", "+00:00"))
                    hours = max((now - published).total_seconds() / 3600, 1)
                except Exception:
                    hours = 72
                c["views"] = views; c["views_per_hour"] = round(views / hours, 1)
        except Exception:
            pass
    candidates.sort(key=lambda x: x.get("views_per_hour", 0), reverse=True)
    top = candidates[:15]
    _save_json("trend_signals.json", top)
    return top


def choose_topic(content_type="short"):
    client = _client()
    trends = trend_research(); analytics = recent_analytics()
    prompt = f"""You are the senior strategist for the USA-focused faceless YouTube channel Vexora Tales.
Today: {datetime.now(TZ).date().isoformat()}
Content: {content_type}
Live trend signals: {json.dumps(trends)[:12000]}
Recent channel analytics: {json.dumps(analytics)[:12000]}
Choose ONE original, realistic, high-interest topic. Never copy a creator or script. Consider topic interest, competition, freshness and retention. Return JSON with topic, angle, hook, reason."""
    r = client.interactions.create(model=TEXT_MODEL, input=prompt)
    text = r.output_text.strip()
    try: result = json.loads(text)
    except Exception: result = {"topic": text, "angle": "original", "hook": "", "reason": "AI-selected"}
    _save_json("last_topic.json", result); return result


def _image(prompt, path, aspect_ratio):
    client = _client()
    interaction = client.interactions.create(model=IMAGE_MODEL, input=prompt, response_format={"type": "image", "aspect_ratio": aspect_ratio, "image_size": "1K"})
    if not interaction.output_image: raise RuntimeError("Image generation returned no image")
    path.write_bytes(base64.b64decode(interaction.output_image.data))


def _tts(script, path):
    client = _client()
    interaction = client.interactions.create(model=TTS_MODEL, input=f"Read this script as a natural, confident American YouTube narrator. Do not add words.\n\n{script}", response_format={"type": "audio"}, generation_config={"speech_config": [{"voice": "Kore"}]})
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(24000); wf.writeframes(base64.b64decode(interaction.output_audio.data))


def _seconds(wav_path):
    with wave.open(str(wav_path), "rb") as w: return w.getnframes() / float(w.getframerate())


def _srt(script, duration):
    words = script.split()
    if not words: return ""
    size = max(8, len(words) // 5); chunks = [words[i:i + size] for i in range(0, len(words), size)]
    lines = []; step = duration / len(chunks)
    for i, chunk in enumerate(chunks):
        a, b = i * step, min(duration, (i + 1) * step)
        def ts(x):
            ms = int(x * 1000); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000); return f"{h:02}:{m:02}:{s:02},{ms:03}"
        lines.append(f"{i+1}\n{ts(a)} --> {ts(b)}\n{' '.join(chunk)}\n")
    return "\n".join(lines)


def _make_video(images, audio, out, vertical=True):
    duration = _seconds(audio); per = duration / len(images); clips = []
    with tempfile.TemporaryDirectory() as td:
        for i, img in enumerate(images):
            clip = Path(td) / f"clip{i}.mp4"
            vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" if vertical else "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080"
            subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-t", str(per), "-vf", vf, "-r", "30", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-an", str(clip)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            clips.append(clip)
        concat = Path(td) / "concat.txt"; concat.write_text("\n".join(f"file '{x}'" for x in clips), encoding="utf-8")
        silent = Path(td) / "silent.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(silent)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        srt = Path(td) / "captions.srt"; srt.write_text(_srt((DATA / "pending_script.txt").read_text(encoding="utf-8"), duration), encoding="utf-8")
        vf2 = f"subtitles={srt}:force_style='FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=80'"
        subprocess.run(["ffmpeg", "-y", "-i", str(silent), "-i", str(audio), "-vf", vf2, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(out)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def generate_video(content_type="short", topic=None):
    client = _client(); vertical = content_type == "short"
    if topic is None: topic = choose_topic(content_type)
    word_target = "65-85" if vertical else "1300-1600"
    script = client.interactions.create(model=TEXT_MODEL, input=f"Create an original American-English faceless YouTube script for Vexora Tales. Topic: {topic.get('topic')} Angle: {topic.get('angle')} Hook: {topic.get('hook')} Length target: {word_target} spoken words. Use a powerful first 2 seconds, visual storytelling, short sentences, curiosity gaps, a satisfying payoff, and no copyrighted material. Return ONLY the narrator script.").output_text.strip()
    (DATA / "pending_script.txt").write_text(script, encoding="utf-8")
    metadata_text = client.interactions.create(model=TEXT_MODEL, input=f"Create JSON metadata for this YouTube video. Return title, description, tags. Title must be curiosity-driven but accurate.\n\nSCRIPT:\n{script}").output_text.strip()
    try: meta = json.loads(metadata_text)
    except Exception: meta = {"title": "Vexora Tales", "description": script[:1000], "tags": ["Vexora Tales", "mystery", "story"]}
    if vertical and "#Shorts" not in meta["title"]: meta["title"] += " #Shorts"
    audio = ASSETS / "voice.wav"; _tts(script, audio); duration = _seconds(audio)
    scene_count = 4 if vertical else max(8, min(12, round(duration / 50)))
    scene_text = client.interactions.create(model=TEXT_MODEL, input=f"Break this script into exactly {scene_count} cinematic visual scenes. Return JSON array, each item having scene and visual_prompt. Keep the same visual world and recurring subjects consistent.\n\nSCRIPT:\n{script}").output_text.strip()
    try: scenes = json.loads(scene_text)
    except Exception: scenes = [{"scene": i + 1, "visual_prompt": f"Cinematic visual illustrating this story, scene {i+1}. {script[:500]}"} for i in range(scene_count)]
    images = []
    for i, scene in enumerate(scenes[:scene_count]):
        p = ASSETS / f"scene_{i+1}.png"
        suffix = ". Photorealistic cinematic documentary style, no text, no logos, 9:16 vertical composition." if vertical else ". Photorealistic cinematic documentary style, no text, no logos, 16:9 composition."
        _image(scene.get("visual_prompt", "") + suffix, p, "9:16" if vertical else "16:9"); images.append(p)
    out = DATA / "pending_video.mp4"; _make_video(images, audio, out, vertical=vertical)
    thumb = DATA / "pending_thumbnail.jpg"; _image(f"Create a dramatic YouTube thumbnail for: {meta['title']}. Photorealistic cinematic scene, strong focal subject, high contrast, no words or logos, 16:9.", thumb, "16:9")
    result = {"video": str(out), "thumbnail": str(thumb), "title": meta["title"], "description": meta.get("description", ""), "tags": meta.get("tags", []), "content_type": content_type, "topic": topic, "created_at": datetime.now(TZ).isoformat(), "approved": False}
    _save_json("pending.json", result); return result


def upload_pending(approved=False):
    pending = _load_json("pending.json")
    if not pending or not Path(pending["video"]).exists(): raise RuntimeError("No pending video. Generate a video first.")
    if not approved: raise RuntimeError("Upload is locked. Approval is required.")
    youtube, _ = youtube_services()
    if not youtube: raise RuntimeError("YouTube is not connected.")
    body = {"snippet": {"title": pending["title"], "description": pending["description"], "tags": pending["tags"], "categoryId": "24", "defaultLanguage": "en", "defaultAudioLanguage": "en"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(pending["video"], mimetype="video/mp4", resumable=True))
    response = None
    while response is None: _, response = request.next_chunk()
    video_id = response["id"]; thumb_error = None
    try: youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(pending["thumbnail"], mimetype="image/jpeg")).execute()
    except Exception as e: thumb_error = str(e)
    result = {"video_id": video_id, "url": f"https://www.youtube.com/watch?v={video_id}", "title": pending["title"], "uploaded_at": datetime.now(TZ).isoformat(), "thumbnail_error": thumb_error}
    _save_json("last_upload.json", result); pending["approved"] = True; _save_json("pending.json", pending); return result


def status_summary():
    return {"channel": channel_status(), "analytics": recent_analytics(), "pending": _load_json("pending.json"), "last_upload": _load_json("last_upload.json")}
