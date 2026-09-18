
import json
import os
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from agent_core import choose_topic, generate_video, status_summary, upload_pending
from command_router import parse_command
from content_plan import schedule_for_day
from copyright_guard import check_originality

st.set_page_config(page_title="Sameena AI", page_icon="🎬", layout="centered")

st.title("🎬 Sameena AI")
st.caption("Vexora Tales — USA-focused faceless YouTube control center")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Bhai, main Sameena hoon. Main Vexora Tales ke USA-focused faceless channel ke liye content plan, trend research, scripts, voice, visuals aur analytics handle karungi. Public upload tumhari explicit approval ke bina nahi hoga."}
    ]

# Recover the pending job from disk after an app restart.
if "pending" not in st.session_state:
    pending_file = Path("data/pending.json")
    if pending_file.exists():
        try:
            st.session_state.pending = json.loads(pending_file.read_text(encoding="utf-8"))
        except Exception:
            st.session_state.pending = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def _plan_text(days=7):
    rows = []
    start = date.today()
    for i in range(days):
        p = schedule_for_day(start + timedelta(days=i))
        rows.append(f"- **{p['day']}** → {p['content_type'].title()} → **{p['target_duration_label']}**")
    return "\n".join(rows)


def reply(text: str):
    t = text.lower().strip()
    cmd = parse_command(text)

    # Natural Hinglish commands are normalized here; execution keeps the existing safety gates.
    if cmd.intent == 'plan_30':
        t = '30 din'
    elif cmd.intent == 'plan':
        t = 'aaj ka plan'
    elif cmd.intent == 'status':
        t = 'status'
    elif cmd.intent == 'trend':
        t = 'trend'
    elif cmd.intent == 'preview':
        t = 'preview'
    elif cmd.intent == 'request_upload':
        t = 'upload'
    elif cmd.intent == 'approve_upload':
        t = 'yes, upload'
    elif cmd.intent == 'generate' and cmd.content_type == 'short':
        t = 'short banao'
    elif cmd.intent == 'generate' and cmd.content_type == 'long':
        t = 'long banao'

    if "30 day" in t or "30-day" in t or "30 din" in t:
        return "**Sameena ka 30-day content plan**\n\n" + _plan_text(30)

    if "plan" in t and ("aaj" in t or "schedule" in t or "next" in t):
        p = schedule_for_day(date.today())
        return f"**Aaj ka plan:** {p['content_type'].title()} — **{p['target_duration_label']}**\n\nNext 7 days:\n{_plan_text(7)}"

    if "aaj kya" in t or "status" in t or "report" in t:
        data = status_summary()
        ch = data.get("channel", {})
        pending = data.get("pending")
        lines = [
            f"**Channel:** {ch.get('channel', 'Not connected')}",
            f"**Subscribers:** {ch.get('subscribers', '—')}",
            f"**Total views:** {ch.get('views', '—')}",
            f"**Videos:** {ch.get('video_count', '—')}",
        ]
        if pending:
            lines.append(f"**Pending video:** {pending.get('title', 'Ready for review')}")
        return "\n\n".join(lines)

    if "topic" in t or "trend" in t or "kya banao" in t:
        topic = choose_topic("short")
        return "**Aaj ka AI-selected USA topic**\n\n" + json.dumps(topic, indent=2)

    if "video dikhao" in t or "show video" in t or "preview" in t:
        pending = st.session_state.get("pending")
        if not pending or not Path(pending.get("video", "")).exists():
            return "Abhi koi pending video nahi hai. Pehle **Ek Short banao** ya **Long video banao**."
        st.session_state.show_preview = True
        return f"🎬 **Preview ready:** {pending.get('title', 'Pending video')}"

    if cmd.intent == "generate":
        content_type = cmd.content_type or "short"
        plan = schedule_for_day(date.today())
        target = cmd.duration_seconds
        if target is None and content_type == plan["content_type"]:
            target = plan["target_duration_seconds"]

        topic = None
        if cmd.topic:
            topic = {
                "topic": cmd.topic,
                "angle": "User-requested topic",
                "hook": "",
                "reason": "User supplied the topic",
            }

        with st.spinner(
            f"Sameena {content_type} video bana rahi hai..."
            " → script → voice → visuals → captions → thumbnail..."
        ):
            result = generate_video(
                content_type,
                topic=topic,
                target_duration_seconds=target,
            )
        st.session_state.pending = result
        return (
            f"✅ **{content_type.title()} video ready hai.**\n\n"
            f"**Title:** {result['title']}\n\n"
            f"**Topic:** {result['topic'].get('topic', '')}\n\n"
            f"**Voice duration:** {result.get('actual_voice_duration_seconds', '—')} sec\n\n"
            "**Upload abhi nahi hua.** Agar aap bolo **'Upload kar do'**, "
            "to originality safety check ke baad final approval maanga jayega."
        )

    if "short" in t and ("banao" in t or "make" in t or "create" in t):
        p = schedule_for_day(date.today())
        with st.spinner(f"Sameena Short bana rahi hai: {p['target_duration_label']} → script → voice → visuals → captions → thumbnail..."):
            result = generate_video("short")
        st.session_state.pending = result
        return f"✅ Short ready hai — target schedule **{p['target_duration_label']}**.\n\n**Title:** {result['title']}\n\n**Topic:** {result['topic'].get('topic', '')}\n\n**Upload abhi nahi hua.** Agar aap bolo **'Upload kar do'**, to originality safety check ke baad approval maanga jayega."

    if "long" in t and ("banao" in t or "make" in t or "create" in t):
        p = schedule_for_day(date.today())
        with st.spinner(f"Sameena long video bana rahi hai: {p['target_duration_label']}..."):
            result = generate_video("long")
        st.session_state.pending = result
        return f"✅ Long video ready hai — scheduled target **{p['target_duration_label']}**.\n\n**Title:** {result['title']}\n\n**Upload abhi nahi hua.**"

    if t in {"yes, upload", "yes upload", "upload yes", "haan upload", "haan, upload kar do"}:
        pending = st.session_state.get("pending")
        if not pending:
            return "Koi pending video nahi hai."
        check = check_originality(pending, "data/pending_script.txt")
        if not check["approved"]:
            return "🛑 Upload blocked by the originality safety gate. Pehle content ko regenerate/review karo."
        if not st.session_state.get("awaiting_upload"):
            return "Pehle **Upload kar do** command do. Uske baad main final approval loongi."
        with st.spinner("YouTube par upload ho raha hai..."):
            result = upload_pending(approved=True)
        st.session_state.awaiting_upload = False
        return f"🚀 **Upload complete**\n\n{result['url']}"

    if "upload" in t:
        pending = st.session_state.get("pending")
        if not pending:
            return "Pehle video banao. Command: **Ek Short banao** ya **Long video banao**."
        check = check_originality(pending, "data/pending_script.txt")
        if not check["approved"]:
            return "🛑 **Upload blocked.**\n\nSameena ko possible reused/copyright-risk signal mila hai, isliye public upload nahi karegi.\n\nSignals: " + ", ".join(check["signals"])
        st.session_state.awaiting_upload = True
        return f"🛡️ **Originality check passed.**\n\n**{pending['title']}**\n\nAgar aap public YouTube upload approve karte ho, type karo: **YES, UPLOAD**."

    return "Main ye commands samajhti hoon:\n\n- **Aaj kya hua?**\n- **Aaj ka trend/topic batao**\n- **Aaj ka plan**\n- **30 din ka plan**\n- **Ek Short banao**\n- **Long video banao**\n- **Video dikhao**\n- **Upload kar do**\n- **YES, UPLOAD**"


prompt = st.chat_input("Sameena ko command do…")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    try:
        answer = reply(prompt)
    except Exception as e:
        answer = f"❌ Kaam complete nahi hua: `{e}`"
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

if st.session_state.get("show_preview"):
    pending = st.session_state.get("pending")
    if pending and Path(pending.get("video", "")).exists():
        st.video(pending["video"])

st.divider()

st.caption(
    "Sameena safety: generated content is not automatically published. "
    "Public upload requires explicit approval and an originality safety check. "
    "Only original/AI-generated or properly licensed assets should be used."
)