import os
import uuid
import json
from typing import Optional

from fastapi import FastAPI, Request, UploadFile, File, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# Import de votre logique métier
from app import logic

# Création de l'application
app = FastAPI(title="Aria CV Coach")

# Configuration des dossiers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Montage des fichiers statiques (CSS, JS, Images)
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Configuration des templates Jinja2
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Gestion des sessions (Stockage temporaire en mémoire pour la démo)
# Dans un environnement de prod, utilisez Redis ou une base de données.
SESSIONS_DB = {}

# Middleware pour sécuriser les cookies de session
# Remplacez "secret-key" par une vraie clé secrète aléatoire
app.add_middleware(SessionMiddleware, secret_key="votre_cle_secrete_super_securisee")

# ==============================================================================
# UTILITAIRES DE SESSION
# ==============================================================================

def get_session_id(request: Request):
    """Récupère l'ID unique de session de l'utilisateur."""
    return request.session.get("uid")

def ensure_session(request: Request):
    """Crée une session si elle n'existe pas."""
    if "uid" not in request.session:
        uid = str(uuid.uuid4())
        request.session["uid"] = uid
        SESSIONS_DB[uid] = {
            "step": 1,
            "data": {},
            "chat_history": []
        }
    return request.session["uid"]

def get_session_data(request: Request):
    """Récupère les données stockées pour l'utilisateur courant."""
    uid = get_session_id(request)
    if not uid or uid not in SESSIONS_DB:
        return None
    return SESSIONS_DB[uid]

# ==============================================================================
# ROUTES (ÉTAPES 1 à 5)
# ==============================================================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirection vers l'étape 1."""
    return RedirectResponse(url="/step1")

# --- ÉTAPE 1 : UPLOAD ---
@app.get("/step1", response_class=HTMLResponse)
async def step1_upload(request: Request):
    ensure_session(request)
    return templates.TemplateResponse("step1_upload.html", {"request": request, "step": 1})

@app.post("/step1", response_class=HTMLResponse)
async def handle_upload(
    request: Request,
    cv_file: UploadFile = File(...),
    url_offre: str = Form(...)
):
    uid = ensure_session(request)
    
    try:
        # Lecture du fichier
        file_bytes = await cv_file.read()
        filename = cv_file.filename
        
        # Appel à la logique (Phase 1)
        # Note : logic.phase_1_analyse sauvegarde sur disque et renvoie des chemins
        resultats_analyse = logic.phase_1_analyse(file_bytes, filename, url_offre, uid)
        
        # Mise à jour de la session
        SESSIONS_DB[uid]["data"].update(resultats_analyse)
        SESSIONS_DB[uid]["step"] = 2
        
        return RedirectResponse(url="/step2", status_code=303)
        
    except Exception as e:
        return templates.TemplateResponse("step1_upload.html", {
            "request": request, 
            "step": 1, 
            "error": f"Erreur lors de l'analyse : {str(e)}"
        })

# --- ÉTAPE 2 : DIAGNOSTIC ---
@app.get("/step2", response_class=HTMLResponse)
async def step2_diagnostic(request: Request):
    session = get_session_data(request)
    if not session: return RedirectResponse(url="/")
    
    # Chargement des données sauvegardées sur disque pour l'affichage
    data = session["data"]
    
    # On récupère les JSON depuis le disque pour les passer au template
    analyse_offre = logic.get_json_from_disk(data.get('analyse_offre_path'))
    evaluation = logic.get_json_from_disk(data.get('evaluation_original_path'))
    
    # Construction de l'objet data complet pour le template
    display_data = {
        "analyse_offre": analyse_offre,
        "evaluation_original": evaluation
    }
    
    score = evaluation.get("score", 0)
    
    return templates.TemplateResponse("step2_diagnostic.html", {
        "request": request, 
        "step": 2, 
        "data": display_data,
        "score": score
    })

@app.post("/step2", response_class=HTMLResponse)
async def handle_diagnostic_decision(request: Request, decision_radio: str = Form(...)):
    uid = get_session_id(request)
    session = SESSIONS_DB.get(uid)
    if not session: return RedirectResponse(url="/")

    # Si l'utilisateur choisit "Alternatives"
    if "ternatives" in decision_radio:  # Match "Chercher des pistes alternatives"
        session["step"] = 4
        return RedirectResponse(url="/step4", status_code=303)
    
    # Sinon "Optimiser" (Phase 2)
    try:
        # Appel à la logique d'optimisation
        session["data"] = logic.phase_2_optimisation(session["data"], uid)
        session["step"] = 3
        return RedirectResponse(url="/step3", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/step2?error={str(e)}", status_code=303)

# --- ÉTAPE 3 : OPTIMISATION & VALIDATION ---
@app.get("/step3", response_class=HTMLResponse)
async def step3_optimize(request: Request):
    session = get_session_data(request)
    if not session: return RedirectResponse(url="/")
    
    data = session["data"]
    
    # Récupération du CV optimisé (texte)
    optimized_cv_text = logic.get_large_text_from_disk(data.get("optimized_cv_path"))
    suggestions = data.get("competences_suggerees", [])
    
    return templates.TemplateResponse("step3_optimize.html", {
        "request": request, 
        "step": 3,
        "data": {"optimized_cv": optimized_cv_text},
        "sugg": suggestions
    })

@app.post("/step3", response_class=HTMLResponse)
async def handle_optimization_validation(request: Request, consent_radio_final: str = Form(...)):
    # Ici, on pourrait ajouter une logique pour intégrer les compétences suggérées si "oui"
    # Pour l'instant, on passe simplement à l'étape finale
    uid = get_session_id(request)
    if uid:
        SESSIONS_DB[uid]["step"] = 5
        
        # Générer les fichiers finaux (PDF/DOCX) maintenant que c'est validé
        try:
            logic.update_fichiers(SESSIONS_DB[uid]["data"], uid)
        except Exception as e:
            print(f"Erreur génération fichiers: {e}")
            
    return RedirectResponse(url="/step5", status_code=303)

# --- ÉTAPE 4 : ALTERNATIVES ---
@app.get("/step4", response_class=HTMLResponse)
async def step4_alternatives(request: Request):
    session = get_session_data(request)
    if not session: return RedirectResponse(url="/")
    
    data = session["data"]
    cv_text = logic.get_large_text_from_disk(data.get("cv_text_path"))
    
    # Génération des alternatives via Mistral
    # On récupère le JSON brut de logic.phase_alternatives
    alternatives_raw = logic.phase_alternatives(cv_text)
    alternatives_json = logic.safe_json_load(alternatives_raw)
    
    # Formatage HTML simple pour l'affichage
    html_content = "<ul>"
    if alternatives_json and "alternatives" in alternatives_json:
        for alt in alternatives_json["alternatives"]:
            html_content += f"<li><strong>{alt}</strong></li>"
    else:
        html_content += f"<li>{alternatives_raw}</li>"
    html_content += "</ul>"

    return templates.TemplateResponse("step4_alternatives.html", {
        "request": request,
        "step": 4,
        "alternatives": html_content
    })

# --- ÉTAPE 5 : FINAL & CHATBOT ---
@app.get("/step5", response_class=HTMLResponse)
async def step5_final(request: Request):
    session = get_session_data(request)
    if not session: return RedirectResponse(url="/")
    
    data = session["data"]
    chat_history = session["chat_history"]
    
    # Chargement des données complètes
    cv_json = logic.get_json_from_disk(data.get("optimized_cv_json_path"))
    cv_text = logic.get_large_text_from_disk(data.get("optimized_cv_path"))
    
    # Recalcul du score (simulation pour l'affichage final, ou reprise de l'ancien)
    evaluation_original = logic.get_json_from_disk(data.get('evaluation_original_path'))
    # On booste le score artificiellement pour montrer l'amélioration (logique démo)
    score_final = min(100, evaluation_original.get("score", 0) + 25)
    
    final_data = {
        "evaluation_optimized": {
            "score": score_final,
            "verdict_court": "Profil optimisé pour l'offre",
            "points_forts": ["Mots-clés ATS intégrés", "Structure professionnelle", "Langage orienté action"]
        },
        "comparaison_versions": {
            "modifications_apportes": ["Reformulation du résumé", "Mise en avant des compétences techniques", "Correction de la structure"]
        },
        "docx_path": data.get("docx_path"),
        "pdf_path": data.get("pdf_path")
    }

    return templates.TemplateResponse("step5_final.html", {
        "request": request,
        "step": 5,
        "data": final_data,
        "cv_content": cv_json if cv_json else {},
        "cv_content_raw": cv_text,
        "chat_history": chat_history
    })

@app.post("/step5", response_class=HTMLResponse)
async def handle_chatbot(request: Request, chat_input: str = Form(...)):
    uid = get_session_id(request)
    session = SESSIONS_DB.get(uid)
    if not session: return RedirectResponse(url="/")
    
    data = session["data"]
    
    # 1. Ajout message utilisateur
    session["chat_history"].append({"role": "user", "content": chat_input})
    
    # 2. Récupération contexte
    current_cv_text = logic.get_large_text_from_disk(data.get("optimized_cv_path"))
    
    # 3. Appel Mistral pour modification
    try:
        prompt_modif = logic.prompt_modification_cv(current_cv_text, chat_input)
        response_mistral = logic.appeler_mistral(prompt_modif)
        json_resp = logic.safe_json_load(response_mistral)
        
        bot_response = ""
        if json_resp and "cv_modifie" in json_resp:
            # Mise à jour du CV sur disque
            new_cv_text = json_resp["cv_modifie"]
            new_path = logic.save_text_to_disk(new_cv_text, uid, f"cv_optimise_v{len(session['chat_history'])}")
            data["optimized_cv_path"] = new_path
            
            # Essayer de mettre à jour la structure JSON aussi (parsing basique)
            # Pour simplifier, on garde le texte brut à jour principalement
            
            changes = json_resp.get("changements_faits", ["Modification appliquée."])
            bot_response = "✅ " + " ".join(changes)
        else:
            bot_response = "❌ Je n'ai pas réussi à modifier le CV correctement. Essayez de reformuler."
            
    except Exception as e:
        bot_response = f"Erreur technique : {str(e)}"
    
    session["chat_history"].append({"role": "assistant", "content": bot_response})
    
    # Recharger la page pour voir les changements
    return RedirectResponse(url="/step5", status_code=303)

# --- AUTRES ROUTES ---

@app.get("/download/{file_type}")
async def download_file(request: Request, file_type: str):
    session = get_session_data(request)
    if not session: return RedirectResponse(url="/")
    
    data = session["data"]
    file_path = data.get(f"{file_type}_path")
    
    if file_path and os.path.exists(file_path):
        filename = f"Mon_CV_Optimise.{file_type}"
        return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')
    
    return HTMLResponse("Fichier non trouvé ou non généré.", status_code=404)

@app.get("/reset")
async def reset_session(request: Request):
    uid = get_session_id(request)
    if uid and uid in SESSIONS_DB:
        # Nettoyage fichiers disque via logic
        logic.clean_session_files(uid)
        del SESSIONS_DB[uid]
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

# Lancement local (si exécuté directement)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)