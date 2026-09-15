import json
import os
import streamlit as st

from agent_core import choose_topic, generate_video, status_summary, upload_pending

st.set_page_config(page_title="Vexora Tales AI", page_icon="🎬", layout="centered")

st.title("🎬 Vexora Tales AI")
st.caption("Your chat-style YouTube control center")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Bhai, main ready hoon. Aap command do: 'Aaj kya hua?', 'Ek Short banao', 'Long video banao', ya 'Upload kar do'. Upload ke liye main approval maangunga."}
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
        return "**Aaj ka AI-selected topic**\n\n" + json.dumps(topic, indent=2)

    if "short" in t and ("banao" in t or "make" in t or "create" in t):
        with st.spinner("Short bana raha hoon: topic → script → voice → visuals → captions → thumbnail..."):
            result = generate_video("short")
        st.session_state.pending = result
        return f"✅ Short ready hai.\n\n**Title:** {result['title']}\n\n**Topic:** {result['topic'].get('topic', '')}\n\n**Upload abhi nahi hua.** Agar aap bolo **'Upload kar do'**, tab approval ke baad upload hoga."

    if "long" in t and ("banao" in t or "make" in t or "create" in t):
        with st.spinner("Long video bana raha hoon..."):
            result = generate_video("long")
        st.session_state.pending = result
        return f"✅ Long video ready hai.\n\n**Title:** {result['title']}\n\n**Upload abhi nahi hua.**"

    if "upload" in t:
        pending = st.session_state.get("pending")
        if not pending:
            return "Pehle video banao. Command: **Ek Short banao** ya **Long video banao**."
        st.session_state.awaiting_upload = True
        return f"⚠️ **Upload approval required.**\n\n**{pending['title']}**\n\nAgar aap sach mein YouTube par public upload karna chahte ho, type karo: **YES, UPLOAD**."

    if t in {"yes, upload", "yes upload", "upload yes", "haan upload", "haan, upload kar do"}:
        pending = st.session_state.get("pending")
        if not pending:
            return "Koi pending video nahi hai."
        with st.spinner("YouTube par upload ho raha hai..."):
            result = upload_pending(approved=True)
        return f"🚀 **Upload complete**\n\n{result['url']}"

    return "Main ye commands samajhta hoon:\n\n- **Aaj kya hua?**\n- **Aaj ka trend/topic batao**\n- **Ek Short banao**\n- **Long video banao**\n- **Upload kar do**\n- **YES, UPLOAD**"

prompt = st.chat_input("Command likho…")
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
st.caption("Safety: video generation does not automatically publish. Public upload requires an explicit approval command.")
