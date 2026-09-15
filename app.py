import json
import os
import streamlit as st

from agent_core import choose_topic, generate_video, status_summary, upload_pending
from copyright_guard import check_originality

st.set_page_config(page_title="Sameena AI", page_icon="🎬", layout="centered")

st.title("🎬 Sameena AI")
st.caption("Vexora Tales — USA-focused faceless YouTube control center")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Bhai, main Sameena hoon. Main Vexora Tales ke USA-focused faceless channel ke liye content plan, trend research, scripts, voice, visuals aur analytics handle karungi. Public upload tumhari explicit approval ke bina nahi hoga."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def reply(text: str):
    t = text.lower().strip()
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

    if "short" in t and ("banao" in t or "make" in t or "create" in t):
        with st.spinner("Sameena Short bana rahi hai: topic → original script → voice → visuals → captions → thumbnail..."):
            result = generate_video("short")
        st.session_state.pending = result
        return f"✅ Short ready hai.\n\n**Title:** {result['title']}\n\n**Topic:** {result['topic'].get('topic', '')}\n\n**Upload abhi nahi hua.** Agar aap bolo **'Upload kar do'**, to originality safety check ke baad approval maanga jayega."

    if "long" in t and ("banao" in t or "make" in t or "create" in t):
        with st.spinner("Sameena long video bana rahi hai..."):
            result = generate_video("long")
        st.session_state.pending = result
        return f"✅ Long video ready hai.\n\n**Title:** {result['title']}\n\n**Upload abhi nahi hua.**"

    if "upload" in t:
        pending = st.session_state.get("pending")
        if not pending:
            return "Pehle video banao. Command: **Ek Short banao** ya **Long video banao**."
        check = check_originality(pending, "data/pending_script.txt")
        if not check["approved"]:
            return "🛑 **Upload blocked.**\n\nSameena ko possible reused/copyright-risk signal mila hai, isliye public upload nahi karegi.\n\nSignals: " + ", ".join(check["signals"])
        st.session_state.awaiting_upload = True
        return f"🛡️ **Originality check passed.**\n\n**{pending['title']}**\n\nVideo is workflow mein AI-generated/original assets ke liye banaya gaya hai; phir bhi YouTube copyright claims ki 100% guarantee koi automated check nahi de sakta.\n\nAgar aap public YouTube upload approve karte ho, type karo: **YES, UPLOAD**."

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

    return "Main ye commands samajhti hoon:\n\n- **Aaj kya hua?**\n- **Aaj ka trend/topic batao**\n- **Ek Short banao**\n- **Long video banao**\n- **Upload kar do**\n- **YES, UPLOAD**"

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

st.divider()
st.caption("Sameena safety: generated content is not automatically published. Public upload requires explicit approval and an originality safety check. Only original/AI-generated or properly licensed assets should be used.")
