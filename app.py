"""
app.py
Streamlit UI for the Ramayana Chatbot powered by Sarvam AI.
Run with: streamlit run app.py
"""

import streamlit as st
from audio_recorder_streamlit import audio_recorder
from rag_chain import ask, speech_to_text, text_to_speech, LANGUAGE_CODES

import os
from seed_knowledge_base import seed as seed_db
if not os.path.exists("./ramayana_db"):
    seed_db()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ramayana Chatbot — Powered by Sarvam AI",
    page_icon="🪔",
    layout="centered"
)

# ── Custom CSS — warm saffron/earth Indian aesthetic ──────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Lato:wght@300;400&display=swap');

  html, body, [class*="css"] {
    font-family: 'Lato', sans-serif;
    background-color: #1a0e05;
    color: #f5e6c8;
  }

  .main-title {
    font-family: 'Cinzel', serif;
    font-size: 2.4rem;
    font-weight: 600;
    color: #f0a500;
    text-align: center;
    letter-spacing: 2px;
    margin-bottom: 0.2rem;
  }

  .subtitle {
    text-align: center;
    color: #c8a97a;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
    font-style: italic;
  }

  .divider {
    border: none;
    border-top: 1px solid #5a3a1a;
    margin: 1rem 0;
  }

  .chat-bubble-user {
    background: #3b1f0a;
    border-left: 3px solid #f0a500;
    padding: 0.8rem 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    color: #f5e6c8;
  }

  .chat-bubble-bot {
    background: #2a1505;
    border-left: 3px solid #c8a97a;
    padding: 0.8rem 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    color: #f5e6c8;
  }

  .speaker-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 4px;
  }

  .user-label  { color: #f0a500; }
  .valmiki-label { color: #c8a97a; }

  .source-box {
    background: #1f1008;
    border: 1px solid #5a3a1a;
    border-radius: 6px;
    padding: 0.6rem 0.8rem;
    font-size: 0.8rem;
    color: #a07850;
    margin-top: 0.3rem;
  }

  .stTextInput > div > div > input {
    background-color: #ffffff !important;
    color: #1a0e05 !important;
    border: 1px solid #5a3a1a !important;
    border-radius: 8px !important;
  }

  .stButton > button {
    background-color: #f0a500;
    color: #1a0e05;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.5rem;
    font-family: 'Cinzel', serif;
    letter-spacing: 1px;
  }

  .stButton > button:hover {
    background-color: #c8860a;
    color: #1a0e05;
  }

  .stSelectbox > div > div {
    background-color: #ffffff !important;
    color: #1a0e05 !important;
    border: 1px solid #5a3a1a !important;
  }

  .stSpinner > div {
    border-top-color: #f0a500 !important;
  }

  footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🪔 Ramayana Chatbot 🪔</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask anything about the Ramayana — in any Indian language</div>', unsafe_allow_html=True)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "language" not in st.session_state:
    st.session_state.language = "English"

if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🌐 Language / भाषा")
    selected_language = st.selectbox(
        "Choose your language",
        options=list(LANGUAGE_CODES.keys()),
        index=list(LANGUAGE_CODES.keys()).index(st.session_state.language)
    )
    st.session_state.language = selected_language

    st.markdown("---")
    st.markdown("### 💡 Sample Questions")
    sample_questions = [
        "Who is Hanuman?",
        "Why was Rama exiled?",
        "How did Sita get abducted?",
        "What is the Lakshmana Rekha?",
        "How was the bridge to Lanka built?",
        "Who wrote the Ramayana?",
        "What happened to Jatayu?",
        "Why did Ravana kidnap Sita?"
    ]
    for q in sample_questions:
        if st.button(q, key=f"sample_{q}"):
            st.session_state["prefill_query"] = q

    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.75rem; color:#7a5a3a;'>Powered by Sarvam AI<br>Sarvam-M · Sarvam Translate<br>ChromaDB · Streamlit</div>",
        unsafe_allow_html=True
    )

# ── Chat history display ──────────────────────────────────────────────────────
for idx, turn in enumerate(st.session_state.chat_history):
    st.markdown(
        f'<div class="chat-bubble-user">'
        f'<div class="speaker-label user-label">You</div>{turn["query"]}'
        f'</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="chat-bubble-bot">'
        f'<div class="speaker-label valmiki-label">🧘 Valmiki says</div>{turn["answer"]}'
        f'</div>',
        unsafe_allow_html=True
    )

    # Show English translation if answer is in a non-English language
    if turn.get("answer") and turn.get("language") and turn["language"] != "English":
        with st.expander("View answer in English", expanded=False):
            from rag_chain import translate_text, LANGUAGE_CODES
            lang_code = LANGUAGE_CODES.get(turn["language"], "en-IN")
            try:
                english_answer = translate_text(turn["answer"], source_lang=lang_code, target_lang="en-IN")
                st.markdown(
                    f'<div class="source-box" style="color:#f5e6c8;">{english_answer}</div>',
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.warning(f"Could not translate: {e}")

    # TTS playback button per answer
    if turn.get("answer"):
        col_play, col_spacer = st.columns([1, 5])
        with col_play:
            if st.button("🔊 Listen", key=f"tts_{idx}"):
                with st.spinner("Generating audio..."):
                    tts_result = text_to_speech(turn["answer"], language=turn["language"])
                if tts_result["error"]:
                    st.error(f"TTS error: {tts_result['error']}")
                else:
                    st.audio(tts_result["audio_bytes"], format="audio/wav")

    # Show source passages in an expander
    if turn.get("passages"):
        with st.expander("📜 Source passages used", expanded=False):
            for i, p in enumerate(turn["passages"], 1):
                st.markdown(
                    f'<div class="source-box">'
                    f'<strong>{i}. {p["topic"]}</strong> — <em>{p["kanda"]}</em><br>{p["text"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )

# ── Input area ────────────────────────────────────────────────────────────────
st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Voice input via microphone ────────────────────────────────────────────────
st.markdown("**🎙️ Speak your question** (click mic, speak, click again to stop)")
audio_bytes = audio_recorder(
    text="",
    recording_color="#f0a500",
    neutral_color="#c8a97a",
    icon_size="2x",
    pause_threshold=3.0
)

if audio_bytes:
    import hashlib
    audio_hash = hashlib.md5(audio_bytes).hexdigest()

    if audio_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = audio_hash
        with st.spinner("Transcribing your voice..."):
            stt_result = speech_to_text(audio_bytes, language=st.session_state.language)

        if stt_result["error"]:
            st.error(f"⚠️ STT error: {stt_result['error']}")
        elif stt_result["transcript"]:
            st.success(f"Heard: *{stt_result['transcript']}*")
            with st.spinner("Consulting the sage Valmiki..."):
                result = ask(stt_result["transcript"], language=st.session_state.language)
            if result["error"]:
                st.error(f"⚠️ Error: {result['error']}")
            else:
                st.session_state.chat_history.append({
                    "query":    f"🎙️ {stt_result['transcript']}",
                    "answer":   result["answer"],
                    "passages": result["passages"],
                    "language": result["language"]
                })
                st.rerun()

st.markdown("**✍️ Or type your question**")

# ── Handle sample question clicks — run immediately without form ──────────────
if "prefill_query" in st.session_state:
    sample_q = st.session_state.pop("prefill_query")
    with st.spinner("Consulting the sage Valmiki..."):
        result = ask(sample_q, language=st.session_state.language)
    if result["error"]:
        st.error(f"⚠️ Error: {result['error']}")
    else:
        st.session_state.chat_history.append({
            "query":    sample_q,
            "answer":   result["answer"],
            "passages": result["passages"],
            "language": result["language"]
        })
    st.rerun()

# ── Manual input form ─────────────────────────────────────────────────────────
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_query = st.text_input(
            label="Ask a question",
            placeholder=f"Ask about the Ramayana in {st.session_state.language}...",
            label_visibility="collapsed"
        )
    with col2:
        submitted = st.form_submit_button("Ask")

if submitted and user_query.strip():
    with st.spinner("Consulting the sage Valmiki..."):
        result = ask(user_query.strip(), language=st.session_state.language)

    if result["error"]:
        st.error(f"⚠️ Error: {result['error']}")
    else:
        st.session_state.chat_history.append({
            "query":    user_query.strip(),
            "answer":   result["answer"],
            "passages": result["passages"],
            "language": result["language"]
        })
        st.rerun()

elif submitted and not user_query.strip():
    st.warning("Please enter a question first.")