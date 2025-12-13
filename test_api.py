# import requests
# import json
# import time
# import os
# from datetime import datetime

# # --- Configuration ---
# API_URL = "http://127.0.0.1:8000/generate_responses"
# INPUT_FILE = "input_questions.json" # Fichier à lire pour les questions
# OUTPUT_DIR = "submission_output"    # Dossier pour enregistrer les fichiers de sortie
# HACKATHON_OUTPUT_FILE = "hackathon_submission.json"
# FRONTEND_OUTPUT_FILE = "frontend_display.json"

# # --- Fonction de Chargement ---

# def load_payload_from_file(file_path):
#     """Charge le JSON d'entrée à partir du fichier spécifié."""
#     try:
#         with open(file_path, 'r', encoding='utf-8') as f:
#             return json.load(f)
#     except FileNotFoundError:
#         print(f"❌ Erreur: Fichier d'entrée '{file_path}' non trouvé.")
#         print("Veuillez créer ce fichier avec le format JSON de vos questions.")
#         return None
#     except json.JSONDecodeError as e:
#         print(f"❌ Erreur: Le fichier '{file_path}' n'est pas un JSON valide.")
#         print(f"Détails de l'erreur: {e}")
#         return None

# # --- Fonction de Sauvegarde ---

# def save_json_file(data, filename, folder=OUTPUT_DIR):
#     """Sauvegarde les données dans un fichier JSON avec formatage."""
#     os.makedirs(folder, exist_ok=True)
#     filepath = os.path.join(folder, filename)
#     with open(filepath, 'w', encoding='utf-8') as f:
#         # Utilisation de ensure_ascii=False pour préserver les caractères arabes/français
#         json.dump(data, f, indent=4, ensure_ascii=False)
#     print(f"✅ Fichier créé : {filepath}")


# # --- Fonction de Test Principale ---

# def run_submission_test():
#     """
#     Charge le JSON d'entrée, interroge l'API, et génère les deux fichiers de sortie.
#     """
    
#     # 1. CHARGEMENT DU PAYLOAD
#     payload = load_payload_from_file(INPUT_FILE)
#     if not payload:
#         return
        
#     # Calcul du nombre total de questions pour la métrique
#     total_questions = sum(len(q) for q in payload['question'].values())
    
#     print(f"🚀 Démarrage du test avec les questions chargées depuis '{INPUT_FILE}'.")
#     print(f"Total des questions à traiter: {total_questions}")
#     print("-" * 50)
    
#     try:
#         start_time = time.time()
        
#         # 2. ENVOI DE LA REQUÊTE
#         response = requests.post(API_URL, json=payload, timeout=90)
#         response.raise_for_status() # Lève une exception si le statut HTTP est 4xx ou 5xx
        
#         end_time = time.time()
        
#         # 3. EXTRACTION DES DEUX FORMATS
#         combined_output = response.json()
        
#         hackathon_data = combined_output.get("hackathon_submission", {})
#         frontend_data = combined_output.get("frontend_display", {})
        
#         if not hackathon_data or not frontend_data:
#             print("❌ Erreur: La réponse de l'API n'a pas les clés 'hackathon_submission' et/ou 'frontend_display'. Vérifiez le code app.py.")
#             return

#         # 4. SAUVEGARDE DES FICHIERS DE SORTIE
        
#         print("\n" + "=" * 20 + " Sauvegarde Hackathon (Format Simple) " + "=" * 13)
#         save_json_file(hackathon_data, HACKATHON_OUTPUT_FILE)
        
#         print("\n" + "=" * 20 + " Sauvegarde Front-End (Format Détaillé) " + "=" * 12)
#         save_json_file(frontend_data, FRONTEND_OUTPUT_FILE)

#         # 5. SYNTHÈSE
#         total_duration = end_time - start_time
#         avg_time_per_q = total_duration / total_questions if total_questions > 0 else 0

#         print("\n" + "=" * 50)
#         print("🎉 Test de soumission réussi! Les deux fichiers JSON ont été générés.")
#         print(f"⚡ Durée totale du traitement: {total_duration:.2f} secondes.")
#         print(f"⏱️ Temps moyen par question: {avg_time_per_q:.2f} secondes.")
#         print(f"Les fichiers se trouvent dans le dossier: ./{OUTPUT_DIR}")
        
#     except requests.exceptions.ConnectionError:
#         print("\n❌ Échec de la connexion. Assurez-vous que l'API est lancée (`uvicorn app:app ...`)")
#     except requests.exceptions.HTTPError as e:
#         print(f"\n❌ Erreur HTTP: {e}")
#         print("Réponse de l'API:\n" + response.text)
#     except requests.exceptions.RequestException as e:
#         print(f"\n❌ Une erreur réseau/inconnue s'est produite: {e}")

# # --- Exécution ---

# if __name__ == "__main__":
#     run_submission_test()


import requests
import json
import time
import os
from datetime import datetime

# --- Configuration ---
API_URL = "http://127.0.0.1:8000/generate_responses"
INPUT_FILE = "input_questions.json"
OUTPUT_DIR = "submission_output"
HACKATHON_OUTPUT_FILE = "hackathon_submission.json"
FRONTEND_OUTPUT_FILE = "frontend_display.json"

# --- Fonction de Chargement ---
def load_payload_from_file(file_path):
    """Charge le JSON d'entrée à partir du fichier spécifié."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Erreur: Fichier d'entrée '{file_path}' non trouvé.")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Erreur: Le fichier '{file_path}' n'est pas un JSON valide.")
        print(f"Détails: {e}")
        return None

# --- Fonction de Sauvegarde ---
def save_json_file(data, filename, folder=OUTPUT_DIR):
    """Sauvegarde les données dans un fichier JSON."""
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✅ Fichier créé : {filepath}")

# --- Fonction de Test Principale ---
def run_submission_test():
    """
    Charge le JSON d'entrée, interroge l'API, et génère les deux fichiers avec timing.
    """
    
    # 1. CHARGEMENT DU PAYLOAD
    payload = load_payload_from_file(INPUT_FILE)
    if not payload:
        return
        
    # Calcul du nombre total de questions
    total_questions = sum(len(q) for q in payload['question'].values())
    
    print("=" * 70)
    print(f"🚀 DÉMARRAGE DU TEST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"📊 Total des questions à traiter: {total_questions}")
    print(f"📂 Fichier d'entrée: {INPUT_FILE}")
    print("-" * 70)
    
    try:
        start_time = time.time()
        
        # 2. ENVOI DE LA REQUÊTE
        print("⏳ Envoi de la requête à l'API...")
        response = requests.post(API_URL, json=payload, timeout=120)
        response.raise_for_status()
        
        end_time = time.time()
        
        # 3. EXTRACTION DES DEUX FORMATS
        combined_output = response.json()
        
        hackathon_data = combined_output.get("hackathon_submission", {})
        frontend_data = combined_output.get("frontend_display", {})
        
        if not hackathon_data or not frontend_data:
            print("❌ Erreur: La réponse de l'API est incomplète.")
            return

        # 4. AFFICHAGE DES MÉTRIQUES DE TIMING
        print("\n" + "=" * 70)
        print("⏱️  MÉTRIQUES DE PERFORMANCE")
        print("=" * 70)
        
        total_api_time = end_time - start_time
        backend_processing_time = frontend_data.get('total_processing_time', 0)
        avg_per_question = frontend_data.get('average_time_per_question', 0)
        
        print(f"📡 Temps total API (réseau + traitement): {total_api_time:.3f}s")
        print(f"⚙️  Temps de traitement backend: {backend_processing_time:.3f}s")
        print(f"📈 Temps moyen par question: {avg_per_question:.3f}s")
        
        # Afficher le timing par question
        print("\n" + "-" * 70)
        print("🔍 DÉTAILS PAR QUESTION:")
        print("-" * 70)
        
        for offer_key, questions in frontend_data.get('reponses_detaillees', {}).items():
            for q_id, details in questions.items():
                gen_time = details.get('generation_time', 0)
                source = details.get('source_document', 'N/A')
                print(f"  • Q{q_id}: {gen_time:.3f}s | Source: {source}")
        
        # 5. SAUVEGARDE DES FICHIERS
        print("\n" + "=" * 70)
        print("💾 SAUVEGARDE DES FICHIERS")
        print("=" * 70)
        
        save_json_file(hackathon_data, HACKATHON_OUTPUT_FILE)
        save_json_file(frontend_data, FRONTEND_OUTPUT_FILE)

        # 6. SYNTHÈSE FINALE
        print("\n" + "=" * 70)
        print("🎉 TEST RÉUSSI!")
        print("=" * 70)
        print(f"✅ {total_questions} questions traitées avec succès")
        print(f"📁 Fichiers générés dans: ./{OUTPUT_DIR}/")
        print(f"⚡ Performance: {total_questions/backend_processing_time:.2f} questions/seconde")
        print("=" * 70)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ÉCHEC: Impossible de se connecter à l'API")
        print("Vérifiez que l'API est lancée: uvicorn app:app --reload")
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ERREUR HTTP: {e}")
        print("Réponse de l'API:")
        print(response.text)
    except requests.exceptions.Timeout:
        print("\n❌ TIMEOUT: La requête a pris trop de temps")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERREUR RÉSEAU: {e}")

# --- Exécution ---
if __name__ == "__main__":
    run_submission_test()