import streamlit as st
import requests
import uuid
from supabase import create_client

# --- Page config ---
st.set_page_config(page_title="AI Tutor", page_icon="🎓")

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("static/รูป.jpg", use_container_width=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
.header-container {
    display: flex; flex-direction: column;
    align-items: center; font-family: 'Poppins', sans-serif;
    margin-bottom: 40px;
}
.title-main {
    font-size: 2.8em; font-weight: 600;
    background: linear-gradient(180deg, #F78DA7, #B43B6B);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.title-sub { font-size: 1em; font-weight: 200; color: #8F8F8F; }
            

</style>
<div class="header-container">
    <div style="display:flex;gap:10px;align-items:baseline">
        <div style="font-size:2em;font-weight:600">Chat with</div>
        <div class="title-main">Girlfriend GPT</div>
    </div>
    <div class="title-sub">made by พ๊อย?</div>
</div>
""", unsafe_allow_html=True)

# --- Supabase client ---
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# --- n8n webhook URL ---
N8N_WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]

# ─────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────

def get_all_chats():
    res = supabase.table("chats") \
        .select("id, title, created_at") \
        .order("created_at", desc=True) \
        .execute()
    return res.data

def create_new_chat():
    res = supabase.table("chats").insert({"title": "New Chat"}).execute()
    return res.data[0]["id"]

def delete_chat(chat_id):
    supabase.table("chats").delete().eq("id", chat_id).execute()

def load_messages(chat_id):
    res = supabase.table("messages") \
        .select("role, content") \
        .eq("chat_id", chat_id) \
        .order("created_at") \
        .execute()
    return res.data

def save_message(chat_id, role, content):
    supabase.table("messages").insert({
        "chat_id": chat_id,
        "role": role,
        "content": content
    }).execute()

def update_chat_title(chat_id, title):
    short = title[:40] + "..." if len(title) > 40 else title
    supabase.table("chats").update({"title": short}).eq("id", chat_id).execute()

# ─────────────────────────────────────────
# n8n CALL (your original logic, unchanged)
# ─────────────────────────────────────────

def call_n8n(user_message: str, session_id: str) -> str:
    payload = {
        "message": user_message,
        "sessionId": session_id
    }
    try:
        res = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=60)
        res.raise_for_status()
        data = res.json()

        if isinstance(data, list):
            if len(data) > 0:
                item = data[0]
                if isinstance(item, dict):
                    return item.get("reply") or item.get("output") or item.get("text") or str(item)
                return str(item)
            return "No response returned."

        if isinstance(data, dict):
            return data.get("reply") or data.get("output") or data.get("text") or str(data)

        return str(data)

    except Exception as e:
        return f"⚠️ Error contacting backend: {e}"

# ─────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎓 AI Tutor")
    st.markdown("---")

    if st.button("✏️ New Chat", use_container_width=True):
        new_id = create_new_chat()
        st.session_state.current_chat_id = new_id
        st.session_state.messages = []
        st.rerun()

    st.markdown("#### Recent Chats")
    chats = get_all_chats()

    if not chats:
        st.caption("No chats yet. Start a new one!")
    else:
        for chat in chats:
            col1, col2 = st.columns([5, 1])
            is_active = chat["id"] == st.session_state.current_chat_id
            label = f"{'💬 ' if is_active else ''}{chat['title']}"

            with col1:
                if st.button(label, key=f"chat_{chat['id']}",
                             use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    st.session_state.current_chat_id = chat["id"]
                    st.session_state.messages = load_messages(chat["id"])
                    st.rerun()

            with col2:
                if st.button("🗑", key=f"del_{chat['id']}"):
                    delete_chat(chat["id"])
                    if st.session_state.current_chat_id == chat["id"]:
                        st.session_state.current_chat_id = None
                        st.session_state.messages = []
                    st.rerun()

# ─────────────────────────────────────────
# MAIN CHAT AREA
# ─────────────────────────────────────────

# No chat selected
if st.session_state.current_chat_id is None:
    with st.chat_message("assistant"):
        st.markdown("""Hi there! 👋 I'm **แฟน gpt**, your personal 'girlfriend' assistant.

Click **✏️ New Chat** in the sidebar to get started, or select a previous chat.

You can ask me to:
- Summarize a topic
- Explain a concept step by step
- Help with homework
- รักคับ รักมาก รักสุดๆ วุ้ว

Let's begin!""")

else:
    # Greeting for empty new chat
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown("Hi! 👋 What would you like to learn today?")

    # Display history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask AI Tutor"):
        # Save & show user message
        save_message(st.session_state.current_chat_id, "user", prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Auto-title from first message
        if len(st.session_state.messages) == 1:
            update_chat_title(st.session_state.current_chat_id, prompt)

        # Call n8n and show reply
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = call_n8n(prompt, st.session_state.current_chat_id)
                st.markdown(reply)

        save_message(st.session_state.current_chat_id, "assistant", reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

        st.rerun()