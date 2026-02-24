# Ramayana Chatbot — Powered by Sarvam AI

A multilingual conversational chatbot about the Ramayana, built with Sarvam AI's Indian language capabilities. Ask questions about the Ramayana in 10 Indian languages — by typing or speaking.
Get answers as text or listen to them in your language.

## Features
- Ask questions about the Ramayana in **10 Indian languages**
- Powered by **Sarvam-M** (24B Indian language LLM)
- **Sarvam Translate** for multilingual input/output
- **ChromaDB** for semantic search over Ramayana passages
- Clean chat UI built with **Streamlit**

🌐 Try It Live
👉 Click here to open the chatbot
(No download or signup required — just click and start asking)


🛠️ Tech Stack
### Component                               Technology
LLM                                         Sarvam-M (24B Indian language model)
Translation                                 Sarvam Translate (mayura:v1)
Speech to Text                              Sarvam Saarika v2.5
Text to Speech                              Sarvam Bulbul v
Vector Database                             ChromaDB
UI                                          Streamlit

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourname/ramayana-chatbot
cd ramayana-chatbot
```

### 2. Create virtual environment (Python 3.11 required)
```bash
py -3.11 -m venv venv311          # Windows
python3.11 -m venv venv311        # Mac/Linux

venv311\Scripts\activate          # Windows
source venv311/bin/activate       # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API key
```
Create a .env file based on .env.example:
bash
cp .env.example .env
SARVAM_API_KEY=your-sarvam-key-here
Get your Sarvam API key from https://dashboard.sarvam.ai
```

### 5. Seed the knowledge base (run once)
```bash
python seed_knowledge_base.py
```

### 6. Run the app
```bash
streamlit run app.py
```

## Project Structure
```
ramayana-chatbot/
├── data/
│   └── passages.json         # Ramayana knowledge base (30 passages)
├── app.py                    # Streamlit UI
├── seed_knowledge_base.py    # Populates ChromaDB
├── rag_chain.py              # RAG pipeline + Sarvam integration
├── .env.example              # API key template
├── .gitignore
└── requirements.txt
```

## Supported Languages
English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi