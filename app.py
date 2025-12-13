
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel, Field
# from typing import Dict, Union, Any
# import uvicorn
# import os
# import sys
# import json
# from datetime import datetime

# sys.path.append(os.path.dirname(os.path.abspath(__file__))) 

# from chatbot_core import OptimizedUniversalBot, initialize_kb

# # --- 1. Configuration Globale ---
# TEAM_NAME = "TensorGirls"

# # --- 2. Modèles de Données Pydantic (Input) ---
# class QuestionCategories(BaseModel):
#     __root__: Dict[str, Dict[str, str]] = Field(..., description="Clé: ID catégorie, Valeur: Dictionnaire d'ID question/question")

# class InputPayload(BaseModel):
#     equipe: str = Field(..., example="IA_Team", description="Nom de l'équipe.")
#     question: QuestionCategories

# # --- 3. Modèles de Données Pydantic (Output HACKATHON - FIXED) ---
# class OutputPayloadHackathon(BaseModel):
#     equipe: str = Field(..., example=TEAM_NAME, description="Nom de l'équipe.")
#     reponses: Dict[str, Dict[str, str]] = Field(..., description="Clé: Nom de l'offre, Valeur: Dictionnaire des réponses.")

# # --- 4. Modèles de Données Pydantic (Output FRONTEND - FIXED) ---
# class AnswerDetailFrontend(BaseModel):
#     reponse: str = Field(..., description="Le texte de la réponse générée.")
#     source_document: str = Field(..., description="Le nom du document source réel.")
#     generation_time: float = Field(..., description="Temps de génération en secondes.")

# class OutputPayloadFrontend(BaseModel):
#     timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Horodatage de la réponse.")
#     equipe: str = Field(..., example=TEAM_NAME, description="Nom de l'équipe.")
#     reponses_detaillees: Dict[str, Dict[str, AnswerDetailFrontend]] = Field(..., description="Clé: Nom de l'offre, Valeur: Dictionnaire des réponses détaillées.")
#     total_processing_time: float = Field(..., description="Temps total de traitement en secondes.")
#     average_time_per_question: float = Field(..., description="Temps moyen par question en secondes.")

# # --- 5. Modèle de Sortie Combiné ---
# class CombinedOutput(BaseModel):
#     hackathon_submission: OutputPayloadHackathon
#     frontend_display: OutputPayloadFrontend

# # --- 6. Initialisation ---
# initialize_kb(force_reindex=False) 

# try:
#     rag_bot = OptimizedUniversalBot()
# except ValueError as e:
#     raise RuntimeError(f"FATAL ERROR: {e}")

# app = FastAPI(
#     title="RAG Chatbot API - Hackathon Forsa",
#     description="Endpoint unique générant deux formats de sortie avec timing détaillé.",
#     version="2.0.0"
# )

# # --- 7. Endpoint Principal (Fixed Format) ---
# @app.post("/generate_responses", response_model=CombinedOutput)
# async def generate_responses(payload: InputPayload):
#     """
#     Traite un lot de questions et retourne deux objets JSON :
#     1. Pour la soumission du hackathon (format simple, sans \n).
#     2. Pour l'affichage Front-End (avec source et timing).
#     """
#     import time
    
#     start_time = time.time()
#     all_questions = payload.question.__root__
    
#     # Structures pour les deux sorties
#     responses_hackathon: Dict[str, str] = {}
#     responses_frontend: Dict[str, AnswerDetailFrontend] = {}
    
#     total_questions = sum(len(questions) for questions in all_questions.values())
    
#     # Parcourir toutes les questions
#     for category_id, questions_by_id in all_questions.items():
#         for question_id, question_text in questions_by_id.items():
#             print(f"-> Processing Q ID {question_id} ({category_id}): {question_text[:30]}...")
            
#             # Appeler le modèle RAG
#             answer, gen_time, source_reelle = rag_bot.ask(question_text) 
            
#             # FIXED: Nettoyer les réponses pour le format JSON
#             cleaned_answer = answer.strip().replace('\n', ' ').replace('\r', ' ')
#             # Normaliser les espaces multiples
#             cleaned_answer = ' '.join(cleaned_answer.split())
            
#             # 1. Format Hackathon (simple, sans \n)
#             responses_hackathon[question_id] = cleaned_answer
            
#             # 2. Format Frontend (détaillé avec la source et timing)
#             responses_frontend[question_id] = AnswerDetailFrontend(
#                 reponse=answer.strip(),  # Garde les \n pour l'affichage frontend
#                 source_document=source_reelle,
#                 generation_time=round(gen_time, 3)
#             )
    
#     total_time = time.time() - start_time
#     avg_time = total_time / total_questions if total_questions > 0 else 0
    
#     # Clé de l'offre
#     OFFER_KEY = "Offre_01"
    
#     # Construction des objets de sortie
#     output_hackathon = OutputPayloadHackathon(
#         equipe=TEAM_NAME,
#         reponses={OFFER_KEY: responses_hackathon}
#     )
    
#     output_frontend = OutputPayloadFrontend(
#         equipe=TEAM_NAME,
#         reponses_detaillees={OFFER_KEY: responses_frontend},
#         total_processing_time=round(total_time, 3),
#         average_time_per_question=round(avg_time, 3)
#     )
    
#     return CombinedOutput(
#         hackathon_submission=output_hackathon,
#         frontend_display=output_frontend
#     )

# # --- 8. Point d'entrée ---
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, Optional
import uvicorn
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__))) 
from chatbot_core import OptimizedUniversalBot, initialize_kb

TEAM_NAME = "TensorGirls"
BASE_PATH = Path(__file__).parent
session_store = {}

# Models
class SimpleQuestion(BaseModel):
    question: str
    session_id: Optional[str] = None

class SimpleResponse(BaseModel):
    answer: str
    source: str
    generation_time: float
    session_id: str

# Initialize
print("🔧 Initializing Knowledge Base...")
initialize_kb(force_reindex=False) 

try:
    rag_bot = OptimizedUniversalBot()
    print("✅ Bot initialized successfully!")
except ValueError as e:
    raise RuntimeError(f"FATAL ERROR: {e}")

app = FastAPI(title="Algérie Télécom RAG API", version="3.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the HTML frontend"""
    html_path = BASE_PATH / "index.html"
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Frontend not found. Create index.html</h1>")

@app.get("/logo.png")
async def serve_logo():
    """Serve the logo file"""
    logo_path = BASE_PATH / "logo.png"
    if logo_path.exists():
        return FileResponse(logo_path)
    raise HTTPException(status_code=404, detail="Logo not found")

@app.post("/ask", response_model=SimpleResponse)
async def ask_question(payload: SimpleQuestion):
    """Main endpoint for questions"""
    import time
    
    session_id = payload.session_id or f"session_{int(time.time() * 1000)}"
    
    if session_id not in session_store:
        session_store[session_id] = {
            "created_at": datetime.now().isoformat(),
            "messages": []
        }
    
    session_store[session_id]["messages"].append({
        "type": "user",
        "content": payload.question,
        "timestamp": datetime.now().isoformat()
    })
    
    print(f"🔍 Question: {payload.question[:50]}...")
    
    try:
        answer, gen_time, source = rag_bot.ask(payload.question, use_cache=True)
        
        session_store[session_id]["messages"].append({
            "type": "bot",
            "content": answer,
            "source": source,
            "generation_time": gen_time,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"✅ Answer generated in {gen_time:.2f}s from {source}")
        
        return SimpleResponse(
            answer=answer,
            source=source,
            generation_time=round(gen_time, 3),
            session_id=session_id
        )
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/documents")
async def list_documents():
    """List available documents"""
    documents = {}
    categories = ["Guide NGBSS", "Convention", "Dépôt Vente", "Offres", "Offres en arabe"]
    
    for category in categories:
        category_path = BASE_PATH / category
        if category_path.exists() and category_path.is_dir():
            documents[category] = [f.name for f in category_path.iterdir() if f.is_file()]
        else:
            documents[category] = []
    
    return documents

@app.get("/download/{category}/{filename:path}")
async def download_file(category: str, filename: str):
    """Download a document"""
    file_path = BASE_PATH / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(path=str(file_path), filename=filename)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "bot_initialized": rag_bot is not None,
        "sessions_active": len(session_store)
    }

if __name__ == "__main__":
    print("🚀 Starting Algérie Télécom Chatbot API...")
    print("🔡 Frontend: http://127.0.0.1:8000")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
