import streamlit as st
import requests

# --- Page config ---
st.set_page_config(page_title="AI Tutor", page_icon="🎓")

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

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
        <div class="title-main">AI Tutor</div>
    </div>
    <div class="title-sub">Powered by Chula AI</div>
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    if st.button("✏️ New chat"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

# --- Session ID for memory (Postgres Chat Memory uses this) ---
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

# --- Init chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- n8n webhook URL ---
N8N_WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]  
# e.g. "https://your-n8n.com/webhook/ai-tutor"

def call_n8n(user_message: str, session_id: str) -> str:
    payload = {
        "message": user_message,
        "sessionId": session_id
    }

    try:
        res = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=60)
        res.raise_for_status()

        data = res.json()

        # If n8n returns a list
        if isinstance(data, list):
            if len(data) > 0:
                item = data[0]
                if isinstance(item, dict):
                    return item.get("reply") or item.get("output") or item.get("text") or str(item)
                return str(item)
            return "No response returned."

        # If normal dict
        if isinstance(data, dict):
            return data.get("reply") or data.get("output") or data.get("text") or str(data)

        return str(data)

    except Exception as e:
        return f"⚠️ Error contacting backend: {e}"
    
# --- Greeting ---
with st.chat_message("assistant"):
    st.markdown("""Hi there! 👋 I'm **AI Tutor**, your personal learning assistant.

To get started, you can ask me to:
- Summarize a topic
- Explain a concept step by step
- Help with homework

Let's begin!""")

# --- Display history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Chat input ---
if prompt := st.chat_input("Ask AI Tutor"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = call_n8n(prompt, st.session_state.session_id)
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})