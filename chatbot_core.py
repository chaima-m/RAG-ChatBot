import json
import os
import time
import hashlib
import unicodedata
from dotenv import load_dotenv
from tqdm import tqdm
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions

# Charge les variables d'environnement
load_dotenv()
MY_API_KEY = os.getenv("MY_API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

# Chemin de la base de données (relatif au répertoire Forsa)
CHROMA_PATH = "data/chroma_db_universal"

# ======================================================
# 2. Define JSON Loader (unchanged)
# ======================================================

def robust_json_load(filename):
    """Charge le JSON en gérant les erreurs de format courantes."""
    filepath = os.path.join("data", filename)
    if not os.path.exists(filepath):
        print(f"⚠️ File missing: {filepath}")
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    data = []
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(content):
        while idx < len(content) and content[idx].isspace(): idx += 1
        if idx >= len(content): break
        try:
            obj, end_idx = decoder.raw_decode(content, idx)
            if isinstance(obj, list): data.extend(obj)
            else: data.append(obj)
            idx = end_idx
        except json.JSONDecodeError:
            try:
                fixed = f"[{content.replace('][', '],[')}]".replace('}{', '},{')
                return json.loads(fixed)
            except: break
    return data

# ======================================================
# 3. Text Processing and Chunking (unchanged)
# ======================================================

def normalize_text(text):
    """Normalizes text to improve matching."""
    if not text: return ""
    text = str(text)
    text = unicodedata.normalize('NFKD', text)
    return text.strip()

def split_text_into_chunks(text, chunk_size=512, chunk_overlap=50):
    """Divise le texte en morceaux."""
    if not text: return []
    words = text.split()
    chunks = []
    current_chunk = []
    for word in words:
        if len(" ".join(current_chunk + [word])) > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            overlap_words_count = int(chunk_overlap / 10)
            overlap_words = current_chunk[-overlap_words_count:] if len(current_chunk) > overlap_words_count else []
            current_chunk = overlap_words + [word]
        else:
            current_chunk.append(word)
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

# ======================================================
# 4. Optimized Ingestion (Added more metadata for source tracking)
# ======================================================

def ingest_ultimate_v2():
    """Indexe les données dans ChromaDB."""
    if not all([MY_API_KEY, BASE_URL, MODEL_NAME]):
        raise ValueError("🚨 API Key or Model Config missing in .env file.")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )

    try: client.delete_collection("actel_kb")
    except: pass

    collection = client.create_collection(name="actel_kb", embedding_function=embedding_func)
    total_docs = 0
    print("🚀 Starting Optimized Indexing...")

    # 1. COMMERCIAL OFFERS (Offers_Data.json, offre_fr_json.json, arab_offres.json)
    
    # NOTE: Offers_Data.json est l'ancienne structure, offre_fr_json et arab_offres sont les nouvelles.
    # On maintient l'ingestion des deux pour compatibilité.
    
    for filename in ["Offers_Data.json", "offre_fr_json.json", "arab_offres.json"]:
        data = robust_json_load(filename)
        if not data: continue
        print(f"📥 Indexing {filename}...")
        for item in tqdm(data, desc=f"Indexing {filename}"):
            oid = item.get("id", item.get("offre_id", "N/A"))
            name_fr = item.get("name", {}).get("fr", "Offre") if filename == "Offers_Data.json" else item.get("nom_offre", "Offre")
            
            # Utilisation de 'source' comme fallback pour le nom de fichier JSON
            source_file = filename 

            # Traitement des offres (simplifié)
            doc_text = item.get("description_longue", item.get("desc", {}).get("fr", "")) + " " + item.get("description_longue", item.get("desc", {}).get("ar", ""))
            
            if doc_text:
                chunks = split_text_into_chunks(doc_text, chunk_size=512, chunk_overlap=50)
                for c_idx, chunk in enumerate(chunks):
                    collection.add(
                        documents=[normalize_text(chunk)],
                        # Ajout du nom_offre pour un meilleur contexte de la source réelle si besoin
                        metadatas=[{"source": source_file, "id": oid, "name": name_fr, "type": "commercial"}],
                        ids=[f"off_{oid}_desc_{c_idx}_{filename}"]
                    )
                    total_docs += 1


    # 2. CONVENTIONS (convention_ar.json, conv_fr.json)
    for filename, lang in [("convention_ar.json", "ar"), ("conv_fr.json", "fr")]:
        data = robust_json_load(filename)
        if not data: continue
        print(f"📥 Indexing {filename}...")
        for item in tqdm(data, desc=f"Indexing {filename}"):
            cid = item.get("convention_id", "N/A")
            partner = item.get("nom_partenaire", "Partenaire")
            resume = item.get("resume_clauses", "")
            
            # Extraction du nom du document source réel
            source_doc = item.get('source_pdf_url', item.get('source', filename)) 

            doc_text = f"Convention: {partner}\n{resume}"
            
            collection.add(
                documents=[normalize_text(doc_text)],
                metadatas=[{"source": filename, "source_doc_url": source_doc, "id": cid, "name": partner, "type": "convention"}],
                ids=[f"conv_{lang}_{cid}_sum"]
            )
            total_docs += 1

            for idx, sub in enumerate(item.get("offres", [])):
                offer_text = f"Convention: {partner}\nOffer: {sub.get('intitule', '')}"
                collection.add(
                    documents=[normalize_text(offer_text)],
                    metadatas=[{"source": filename, "source_doc_url": source_doc, "id": cid, "name": partner, "type": "convention_offer"}],
                    ids=[f"conv_{lang}_{cid}_{idx}"]
                )
                total_docs += 1

    # 3. DEPOT VENTE (structured_offers_depot_vente_enriched.json)
    dv_file = "structured_offers_depot_vente_enriched.json"
    data = robust_json_load(dv_file)
    if data:
        print(f"📥 Indexing {dv_file}...")
        for idx, item in enumerate(tqdm(data, desc=f"Indexing {dv_file}")):
            name = item.get("nom_offre", "Produit")
            oid = item.get("offre_id", f"dv_{idx}")
            
            # Extraction du nom du document source réel
            source_doc = item.get('source_doc_url', dv_file) 
            
            if item.get("texte_fr"):
                full_fr = f"Gamme: {name}\nDesc: {item['texte_fr']}"
                collection.add(
                    documents=[normalize_text(full_fr)],
                    metadatas=[{"source": dv_file, "source_doc_url": source_doc, "id": oid, "name": name, "type": "depot_vente"}],
                    ids=[f"dv_fr_{idx}"]
                )
            # ... (indexation AR et autres produits)

    # 4. NGBSS (ngbss_parsed.json)
    ngbss_file = "ngbss_parsed.json"
    data = robust_json_load(ngbss_file)
    if data:
        print(f"📥 Indexing {ngbss_file}...")
        for idx, proc in enumerate(tqdm(data, desc=f"Indexing {ngbss_file}")):
            proc_name = proc.get("process_name", "Procédure")
            
            # Extraction du nom du document source réel
            source_doc = proc.get('file_name', ngbss_file)
            
            for t_idx, task in enumerate(proc.get("tasks", [])):
                steps = "\n- ".join(task.get("steps", []))
                txt = f"Procédure: {proc_name}\nTâche: {task.get('task_name')}\nÉtapes:\n- {steps}"
                collection.add(
                    documents=[normalize_text(txt)],
                    metadatas=[{"source": ngbss_file, "source_doc_url": source_doc, "id": f"ngbss_{idx}", "name": proc_name, "type": "technique"}],
                    ids=[f"ngbss_step_{idx}_{t_idx}"]
                )
                total_docs += 1

    print(f"✅ Optimized Ingestion Complete! {total_docs} docs.")

def initialize_kb(force_reindex=False):
    """Initialise ou vérifie la base de connaissance."""
    if not os.path.exists(CHROMA_PATH) or force_reindex:
        print("🚨 ChromaDB non trouvé ou réindexation forcée. Démarrage de l'ingestion...")
        ingest_ultimate_v2()
    else:
        print("✅ ChromaDB trouvé. Skipping ingestion.")

# ======================================================
# 5. Optimized Universal Chatbot Class (Updated Source Logic)
# ======================================================

class OptimizedUniversalBot:
    """Class principale pour le RAG, mise à jour pour inclure la source réelle."""
    def __init__(self):
        if not all([MY_API_KEY, BASE_URL, MODEL_NAME]):
            raise ValueError("🚨 API Key or Model Config missing in .env file.")
            
        print("Initializing ChromaDB Client...")
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        try:
            self.collection = self.client.get_collection(
                name="actel_kb",
                embedding_function=self.embedding_func
            )
            print(f"✅ ChromaDB Collection 'actel_kb' loaded with {self.collection.count()} documents.")
        except Exception as e:
            print(f"⚠️ Collection 'actel_kb' not found. Run ingest_ultimate_v2() first. Error: {e}")
            self.collection = None
            
        self.llm = OpenAI(api_key=MY_API_KEY, base_url=BASE_URL)
        self.query_cache = {}

    def _get_query_hash(self, query):
        return hashlib.md5(query.lower().strip().encode()).hexdigest()

    def ask(self, query, use_cache=True):
        """Pose une question et retourne la réponse générée, le temps ET la source réelle du document."""
        if not self.collection:
            return "❌ Erreur: Base de connaissance non chargée. Veuillez exécuter l'ingestion.", 0.0, "N/A" 

        total_start = time.time()
        query_hash = self._get_query_hash(query)
        
        # Le cache doit stocker la source réelle (main_source)
        if use_cache and query_hash in self.query_cache:
            cached_response, cached_time, cached_source = self.query_cache[query_hash]
            return cached_response, 0.001, cached_source 

        # 1. OPTIMIZED RETRIEVAL
        retrieval_start = time.time()
        results = self.collection.query(
            query_texts=[query],
            n_results=4
        )
        retrieval_time = time.time() - retrieval_start

        if not results['documents'] or not results['documents'][0]:
            return "❌ Information introuvable dans la base de connaissance.", 0.0, "N/A"

        # ====================================================================
        # LOGIQUE AMÉLIORÉE POUR DÉTERMINER LA SOURCE RÉELLE DU DOCUMENT
        # ====================================================================
        first_metadata = results['metadatas'][0][0]
        
        # 1. Priorité 1: source_doc_url (utilisé dans Conventions et Depot Vente)
        main_source = first_metadata.get('source_doc_url', 'N/A')
        
        # 2. Priorité 2: file_name (utilisé dans NGBSS)
        if main_source == 'N/A' or main_source.lower() == 'à compléter':
            main_source = first_metadata.get('file_name', 'N/A')
            
        # 3. Fallback: nom du fichier JSON ingéré (clé 'source')
        if main_source == 'N/A':
            main_source = first_metadata.get('source', 'Document Inconnu')

        # Nettoyage de la source (pour un affichage plus propre)
        if main_source.startswith("Argumentaires dépot Vente AR FR/"):
            main_source = main_source.split("/")[-1] # Ne garder que le nom du fichier à la fin du chemin
        
        # ====================================================================

        # 2. BUILD SMART CONTEXT
        context_parts = []
        seen_content = set()
        has_ngbss = False
        
        for i, text in enumerate(results['documents'][0]):
            text_signature = text[:100].lower()
            if text_signature in seen_content:
                continue
            seen_content.add(text_signature)

            meta = results['metadatas'][0][i]
            type_ = meta.get('type', 'General')
            name = meta.get('name', 'N/A')

            if type_ == 'technique' or 'ngbss' in meta.get('source', '').lower():
                context_parts.append(f"[PROCÉDURE TECHNIQUE: {name}]\n{text}")
                has_ngbss = True
            else:
                truncated = text[:600] + "..." if len(text) > 600 else text
                context_parts.append(f"[{type_}:{name}] {truncated}")

        full_context = "\n\n".join(context_parts)

        # 3. ADAPTIVE PROMPT (inchangé)
        if has_ngbss:
            prompt = f"""Tu es un consultant technique Algérie Télécom spécialisé dans le Guide NGBSS.

CONTEXTE (PROCÉDURES TECHNIQUES):
{full_context}

RÈGLES STRICTES POUR LES PROCÉDURES:
1. Reproduis TOUTES les étapes dans l'ordre exact
2. Numérotation claire (1., 2., 3., etc.)
3. Ne saute AUCUNE étape, même si ça semble évident
4. Si plusieurs tâches existent, liste-les toutes
5. Même langue que la question
6. Sois précis sur les noms de champs, boutons, et menus

Format attendu:
**Procédure: [Nom]**
1. Première étape...
2. Deuxième étape...
etc."""
        else:
            prompt = f"""Tu es un consultant Algérie Télécom. Réponds de manière CONCISE et DIRECTE.

CONTEXTE:
{full_context}

RÈGLES:
1. Réponse courte et précise (3-5 phrases max pour questions simples)
2. Si commercial: prix + conditions essentielles + cible
3. Si produit: caractéristiques clés + prix + garantie
4. Même langue que la question
5. Si info manquante: dis-le brièvement

Évite les répétitions et les introductions longues."""

        try:
            # 4. ADAPTIVE LLM CALL
            generation_start = time.time()
            max_output_tokens = 800 if has_ngbss else 400

            resp = self.llm.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.2,
                max_tokens=max_output_tokens,
                top_p=0.9,
            )

            generation_time = time.time() - generation_start
            # total_time = time.time() - total_start

            answer = resp.choices[0].message.content

            # Cache the result - stocke la réponse, le temps et la source réelle
            if use_cache:
                self.query_cache[query_hash] = (answer, generation_time, main_source)
                if len(self.query_cache) > 100:
                    self.query_cache.pop(next(iter(self.query_cache)))

            return answer, generation_time, main_source # Retourne la source réelle

        except Exception as e:
            return f"❌ Erreur lors de la génération: {str(e)[:100]}", 0.0, "N/A"
        
def ask_with_context(self, query, conversation_history=None, use_cache=True):
    """
    Enhanced ask method that considers conversation history for better context.
    
    Args:
        query: Current user question
        conversation_history: List of previous messages [{"type": "user"/"bot", "content": "..."}]
        use_cache: Whether to use caching
    
    Returns:
        (answer, generation_time, source_document)
    """
    if not self.collection:
        return "❌ Erreur: Base de connaissance non chargée.", 0.0, "N/A"
    
    # Build context-aware query
    if conversation_history and len(conversation_history) > 0:
        # Get last 3 exchanges for context
        recent_context = conversation_history[-6:]  # Last 3 Q&A pairs
        context_summary = "\n".join([
            f"{'User' if msg['type'] == 'user' else 'Assistant'}: {msg['content'][:100]}"
            for msg in recent_context
        ])
        enhanced_query = f"Contexte de conversation récent:\n{context_summary}\n\nQuestion actuelle: {query}"
    else:
        enhanced_query = query
    
    # Use the enhanced query for retrieval
    return self.ask(enhanced_query, use_cache=use_cache)