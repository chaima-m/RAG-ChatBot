# TensorGirls
Smart Front Office Assistant An intelligent assistant designed to analyze client needs and instantly suggest relevant commercial offers and partner agreements. It streamlines Front Office workflows, reduces manual effort, and improves response time and service quality.
# Algérie Télécom - RAG Chatbot

## 📌 Overview
A Retrieval-Augmented Generation (RAG) chatbot for Algérie Télécom agents. Answers questions about offers, conventions, NGBSS procedures, and depot products in French/Arabic.

---

## ✨ Features
- **Smart RAG Chatbot**: Natural language Q&A in French & Arabic
- **Multi-source Integration**: Commercial offers, conventions, NGBSS guide, depot products
- **Dual API Format**: Hackathon submission + frontend display formats
- **Web Interface**: Responsive chat interface with source tracking
- **Performance**: <3s response time with caching

---

## ⚠️ Limitations
- **Fixed retrieval**: Always returns 4 chunks
- **Basic Arabic support**: Same model as French
- **No conversation memory**: Limited context
- **Manual reindexing**: Requires command to update KB
- **Local deployment only**: No cloud setup

---

## 🛠️ Tech Stack
**Backend**: FastAPI, Python  
**AI/ML**: ChromaDB, Sentence Transformers, OpenAI-compatible API  
**Data**: PyMuPDF, Tesseract OCR, JSON  
**Frontend**: HTML5, CSS3, Vanilla JS  
**Tools**: Uvicorn, dotenv, tqdm, pydantic

---

## 🚀 Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Setup env
cp .env.example .env
# Edit .env with API credentials

# 3. Initialize KB
python -c "from chatbot_core import initialize_kb; initialize_kb()"

# 4. Run
uvicorn app:app --reload

# Access:
# - App: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

---

## 📁 Project Structure
```
app.py              # FastAPI app
chatbot_core.py     # RAG logic
index.html         # Frontend
requirements.txt   # Dependencies
test_api.py       # Testing
input_questions.json  # Sample questions
```

---

## 📊 API Endpoints
- `POST /generate_responses` - Main endpoint (dual format)
- `GET /` - Frontend interface
- `POST /ask` - Single question endpoint
- `GET /download/{category}/{file}` - Document download

---

## 🧪 Testing
```bash
python test_api.py
# Outputs: submission_output/hackathon_submission.json
#          submission_output/frontend_display.json
```

---

---

*Team TensorGirls - Forsa Hackathon 2025*
