"""
rag_chain.py
Core RAG pipeline:
  1. Detect + translate user query to English (via Sarvam Translate)
  2. Retrieve relevant passages from ChromaDB
  3. Generate answer using Sarvam-M LLM
  4. Translate answer back to user's language (via Sarvam Translate)
"""

import os
import base64
import requests
import chromadb
from sarvamai import SarvamAI
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
sarvam_client  = SarvamAI(api_subscription_key=SARVAM_API_KEY)
DB_PATH        = "./ramayana_db"
COLLECTION     = "ramayana_passages"

# Supported languages: display name → Sarvam language code
LANGUAGE_CODES = {
    "English":    "en-IN",
    "Hindi":      "hi-IN",
    "Tamil":      "ta-IN",
    "Telugu":     "te-IN",
    "Kannada":    "kn-IN",
    "Malayalam":  "ml-IN",
    "Bengali":    "bn-IN",
    "Marathi":    "mr-IN",
    "Gujarati":   "gu-IN",
    "Punjabi":    "pa-IN",
}

# ── ChromaDB client (lazy loaded) ────────────────────────────────────────────
_collection = None

def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=DB_PATH)
        _collection = client.get_collection(COLLECTION)
    return _collection


# ── Sarvam Translate ─────────────────────────────────────────────────────────
def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text using Sarvam's mayura:v1 model."""
    if source_lang == target_lang:
        return text

    url = "https://api.sarvam.ai/translate"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "input":               text,
        "source_language_code": source_lang,
        "target_language_code": target_lang,
        "model":               "mayura:v1",
        "mode":                "formal"
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json().get("translated_text", text)


# ── ChromaDB retrieval ────────────────────────────────────────────────────────
def retrieve_passages(query_en: str, n_results: int = 3) -> list[dict]:
    """Retrieve top-n relevant Ramayana passages for an English query."""
    collection = get_collection()
    results = collection.query(
        query_texts=[query_en],
        n_results=n_results
    )

    passages = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        passages.append({
            "text":       doc,
            "kanda":      meta.get("kanda", ""),
            "topic":      meta.get("topic", ""),
            "characters": meta.get("characters", "")
        })
    return passages


# ── Sarvam-M Chat Completion ──────────────────────────────────────────────────
def generate_answer(query_en: str, passages: list[dict]) -> str:
    """Generate answer using Sarvam-M with retrieved passages as context."""

    # Build context block from retrieved passages
    context_parts = []
    for i, p in enumerate(passages, 1):
        context_parts.append(
            f"[Passage {i} — {p['kanda']}, Topic: {p['topic']}]\n{p['text']}"
        )
    context = "\n\n".join(context_parts)

    system_prompt = (
        "You are Valmiki, the sage-poet and author of the Ramayana. "
        "You have deep knowledge of all events, characters, and teachings of the Ramayana. "
        "Answer questions thoughtfully and accurately based on the provided context passages. "
        "If the context does not contain enough information, draw on your knowledge of the Ramayana. "
        "Keep answers concise (3-5 sentences) unless the question requires detail. "
        "Always respond in English — the response will be translated separately."
    )

    user_message = (
        f"Context from the Ramayana:\n\n{context}\n\n"
        f"Question: {query_en}\n\n"
        f"Answer as Valmiki the sage:"
    )

    url = "https://api.sarvam.ai/v1/chat/completions"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sarvam-m",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ],
        "max_tokens": 512
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


# ── Main RAG pipeline ─────────────────────────────────────────────────────────
def ask(query: str, language: str = "English") -> dict:
    """
    Full RAG pipeline:
      query    — user's question (in any supported language)
      language — user's selected language (display name from LANGUAGE_CODES)

    Returns dict with: answer, source_passages, language
    """
    lang_code = LANGUAGE_CODES.get(language, "en-IN")

    try:
        # Step 1: Translate query to English for retrieval + generation
        query_en = query
        if lang_code != "en-IN":
            query_en = translate_text(query, source_lang=lang_code, target_lang="en-IN")

        # Step 2: Retrieve relevant passages
        passages = retrieve_passages(query_en, n_results=3)

        # Step 3: Generate answer in English using Sarvam-M
        answer_en = generate_answer(query_en, passages)

        # Step 4: Translate answer back to user's language
        answer = answer_en
        if lang_code != "en-IN":
            answer = translate_text(answer_en, source_lang="en-IN", target_lang=lang_code)

        return {
            "answer":    answer,
            "passages":  passages,
            "language":  language,
            "query_en":  query_en,   # for debugging
            "error":     None
        }

    except requests.exceptions.HTTPError as e:
        error_msg = f"API error: {e.response.status_code} — {e.response.text}"
        return {"answer": None, "passages": [], "language": language, "error": error_msg}

    except Exception as e:
        return {"answer": None, "passages": [], "language": language, "error": str(e)}


# ── Speech-to-Text (Saarika v2.5) ─────────────────────────────────────────────
def speech_to_text(audio_bytes: bytes, language: str = "English") -> dict:
    """
    Transcribe audio bytes to text using Sarvam's Saarika model.
    audio_bytes — raw WAV audio bytes (from mic recorder)
    language    — user's selected language (display name)
    Returns dict with: transcript, language_code, error
    """
    lang_code = LANGUAGE_CODES.get(language, "en-IN")

    try:
        url = "https://api.sarvam.ai/speech-to-text"
        headers = {"api-subscription-key": SARVAM_API_KEY}
        files   = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        data    = {
            "model":         "saarika:v2.5",
            "language_code": lang_code
        }

        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        result = response.json()

        return {
            "transcript":     result.get("transcript", ""),
            "language_code":  result.get("language_code", lang_code),
            "error":          None
        }

    except requests.exceptions.HTTPError as e:
        return {"transcript": "", "language_code": lang_code, "error": f"STT error: {e.response.status_code} — {e.response.text}"}
    except Exception as e:
        return {"transcript": "", "language_code": lang_code, "error": str(e)}


# ── Text-to-Speech (Bulbul v3) ────────────────────────────────────────────────

# Map language display name to a good default Bulbul voice
TTS_VOICES = {
    "English":   "shubh",
    "Hindi":     "anushka",
    "Tamil":     "abhilasha",
    "Telugu":    "anushka",
    "Kannada":   "anushka",
    "Malayalam": "anushka",
    "Bengali":   "anushka",
    "Marathi":   "anushka",
    "Gujarati":  "anushka",
    "Punjabi":   "anushka",
}

def text_to_speech(text: str, language: str = "English") -> dict:
    """
    Convert text to speech using Sarvam's Bulbul v3 model.
    text     — the answer text to speak
    language — user's selected language (display name)
    Returns dict with: audio_bytes (WAV), error
    """
    lang_code = LANGUAGE_CODES.get(language, "en-IN")
    speaker   = TTS_VOICES.get(language, "shubh")

    # Bulbul v3 limit is 2500 chars — truncate gracefully if needed
    if len(text) > 2500:
        text = text[:2490] + "..."

    try:
        response = sarvam_client.text_to_speech.convert(
            text=text,
            target_language_code=lang_code,
            model="bulbul:v3",
            speaker=speaker
        )

        # Response contains base64-encoded audio — decode to bytes
        audio_base64 = response.audios[0]
        audio_bytes  = base64.b64decode(audio_base64)

        return {"audio_bytes": audio_bytes, "error": None}

    except Exception as e:
        return {"audio_bytes": None, "error": str(e)}