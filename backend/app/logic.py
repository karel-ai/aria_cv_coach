import os
import re
import json
import PyPDF2
import docx2txt
import requests
import glob
from io import BytesIO
from mistralai import Mistral
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Importation des modules existants
from export_cv import creer_docx_cv, creer_pdf_cv
from rag_reformulation_cv import rag_retrieval_sbbert

# ==========================
# CONFIGURATION
# ==========================
load_dotenv()
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
MODEL = "mistral-small-latest"
client = Mistral(api_key=MISTRAL_API_KEY)
print(f"[LOGIC] Utilisation du modèle Mistral : {MODEL}")

# Dossier temporaire pour stocker les textes volumineux
TEMP_DIR = os.path.join(os.getcwd(), "temp_data")
os.makedirs(TEMP_DIR, exist_ok=True)

# ==========================
# GESTION STOCKAGE DISQUE (VITAL POUR FLASK)
# ==========================
def save_text_to_disk(text, session_id, suffix):
    """Sauvegarde un texte long sur le disque."""
    if not text: return None
    filename = f"{session_id}_{suffix}.txt"
    path = os.path.join(TEMP_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(text))
    return path

def get_large_text_from_disk(path):
    """Lit un fichier texte depuis le disque."""
    if not path or not os.path.exists(path): return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save_json_to_disk(data, session_id, suffix):
    """Sauvegarde un dictionnaire JSON sur le disque."""
    if not data: return None
    filename = f"{session_id}_{suffix}.json"
    path = os.path.join(TEMP_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

def get_json_from_disk(path):
    """Lit un fichier JSON depuis le disque."""
    if not path or not os.path.exists(path): return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_session_files(session_id):
    """Nettoie tous les fichiers temporaires liés à une session."""
    for ext in ["txt", "json"]:
        pattern = os.path.join(TEMP_DIR, f"{session_id}_*.{ext}")
        for f in glob.glob(pattern):
            try:
                os.remove(f)
            except OSError:
                pass

# ==========================
# UTILITAIRES D'EXTRACTION
# ==========================
def lire_fichier_upload(file_storage):
    return file_storage.read(), file_storage.filename.lower()

def extraire_texte_pdf(file_bytes):
    try:
        reader = PyPDF2.PdfReader(BytesIO(file_bytes))
        return "".join([page.extract_text() or "" for page in reader.pages])
    except Exception as e:
        raise Exception(f"Erreur PDF : {e}")

def extraire_texte_docx(file_bytes):
    try:
        return docx2txt.process(BytesIO(file_bytes))
    except Exception as e:
        raise Exception(f"Erreur DOCX : {e}")

def extraire_offre_depuis_url(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        r = requests.get(url, timeout=15, headers=headers)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Nettoyage
        for element in soup(["script", "style", "header", "footer", "nav", "iframe", "noscript", "svg"]):
            element.decompose()
            
        text = soup.get_text(separator=' ')
        return re.sub(r'\s+', ' ', text).strip()[:25000]
    except Exception as e:
        raise Exception(f"Erreur scraping offre : {e}")

def appeler_mistral(prompt):
    if not MISTRAL_API_KEY: raise Exception("Clé API manquante.")
    try:
        resp = client.chat.complete(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content
    except Exception as e:
        raise Exception(f"API Mistral : {e}")

def safe_json_load(text: str):
    if not text: return None
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif text.startswith("```"):
        text = text.strip("`").strip()
    try:
        return json.loads(text)
    except:
        return None

def json_cv_to_text(data_json):
    """Convertit le JSON structuré en texte lisible."""
    if not data_json: 
        return ""
    
    # Si c'est déjà du texte
    if isinstance(data_json, str): 
        return data_json
    
    # Si c'est un dict avec cv_optimise_complet imbriqué
    if isinstance(data_json, dict) and 'cv_optimise_complet' in data_json:
        data_json = data_json['cv_optimise_complet']
    
    txt = ""
    ent = data_json.get('entete', {})
    
    # Formatage propre du contact
    nom = ent.get('prenom_nom', '').upper()
    contact_raw = ent.get('contact_info', '')
    
    if isinstance(contact_raw, dict):
        contact_str = " | ".join([str(v) for v in contact_raw.values() if v])
    elif isinstance(contact_raw, list):
        contact_str = " | ".join([str(v) for v in contact_raw if v])
    else:
        contact_str = str(contact_raw)
        
    txt += f"{nom}\n{contact_str}\n\n"
    
    if data_json.get('resume'):
        txt += f"PROFIL __________________________________________________\n{data_json['resume']}\n\n"
        
    if data_json.get('experiences'):
        txt += "EXPERIENCES _____________________________________________\n"
        for e in data_json['experiences']:
            txt += f"{e.get('poste')} @ {e.get('entreprise')} ({e.get('dates')})\n"
            taches = e.get('taches', [])
            if isinstance(taches, list):
                for t in taches: txt += f"- {t}\n"
            else:
                txt += f"- {taches}\n"
            txt += "\n"
            
    if data_json.get('formation'):
        txt += "FORMATION _______________________________________________\n"
        for f in data_json['formation']:
            txt += f"{f.get('diplome')} - {f.get('ecole')} ({f.get('dates')})\n"
            
    txt += "COMPÉTENCES & DIVERS ____________________________________\n"
    
    def add_sec(key, title):
        val = data_json.get(key)
        if val:
            if isinstance(val, list): val = ", ".join(val)
            return f"{title}: {val}\n"
        return ""
    
    txt += add_sec('competences_techniques', 'Tech')
    txt += add_sec('soft_skills', 'Soft Skills')
    txt += add_sec('langues', 'Langues')
    
    return txt

def update_fichiers(data, session_id):
    """Génère les fichiers DOCX et PDF."""
    try:
        payload = None
        # 1. Priorité au JSON structuré
        if data.get('optimized_cv_json_path'):
            payload = get_json_from_disk(data['optimized_cv_json_path'])
        
        # 2. Fallback texte
        if not payload and data.get('optimized_cv_path'):
            payload = get_large_text_from_disk(data['optimized_cv_path'])

        if payload:
            data['docx_path'] = creer_docx_cv(payload)
            data['pdf_path'] = creer_pdf_cv(payload)
    except Exception as e:
        print(f"Erreur update_fichiers: {e}")

# ==========================
# PROMPTS — OPTIMISÉS POUR MISTRAL-SMALL-LATEST
# ==========================

MAX_OFFRE_CHARS = 6000      # idéal pour small-latest
MAX_CV_CHARS = 10000       # éviter les overflow
MAX_RAG_CHARS = 800         # très court pour éviter perte de contrôle

def _truncate(text, limit=MAX_CV_CHARS):
    """Coupe le texte proprement pour éviter les dépassements de contexte."""
    if not text: return ""
    return text[:limit] + "..." if len(text) > limit else text


# ---------------------------------------------------
# 1. Analyse d'offre (compact, JSON strict)
# ---------------------------------------------------
def prompt_analyse_offre(texte_offre):
    return f"""
    Tu es un expert en recrutement. Analyse l'offre d'emploi suivante et retourne UNIQUEMENT un objet JSON STRICT.
    JSON doit contenir les clés :
    - competences_cles (list[str]): 5 à 8 compétences techniques/comportementales.
    - missions_principales (list[str]): 3 à 5 missions clés.
    - mots_cles_ats (list[str]): 10 mots-clés ATS.
    - titre_poste (str): Le titre du poste déduit.

    OFFRE :
    {texte_offre}
    """


# ---------------------------------------------------
# 2. Evaluation du CV
# ---------------------------------------------------

def prompt_evaluer_cv(texte_cv, analyse_offre, role="évaluer"):
    cv = _truncate(texte_cv)
    
    # Convertir analyse_offre en texte lisible si c'est un dict
    if isinstance(analyse_offre, dict):
        offre_text = ""
        if 'titre_poste' in analyse_offre:
            offre_text += f"Titre du poste: {analyse_offre['titre_poste']}\n"
        if 'competences_cles' in analyse_offre:
            offre_text += f"Compétences clés: {', '.join(analyse_offre['competences_cles'][:5])}\n"
        if 'missions_principales' in analyse_offre:
            offre_text += f"Missions: {', '.join(analyse_offre['missions_principales'][:3])}\n"
    else:
        offre_text = str(analyse_offre)[:1000]
    
    return f"""
    Tu es un recruteur expert. {role.capitalize()} ce CV par rapport à l'offre d'emploi ci-dessous.

    RÉPONDS UNIQUEMENT AVEC UN OBJET JSON VALIDE. Format exact :
    {{
      "score": 0,
      "points_forts": ["", "", ""],
      "points_faibles": ["", "", ""],
      "verdict_court": "",
      "recommandations": ["", "", ""]
    }}

    RÈGLES IMPORTANTES :
    1. "score" : nombre entier entre 0 et 100 (pourcentage de correspondance)
    2. "points_forts" : EXACTEMENT 3 points forts spécifiques
    3. "points_faibles" : EXACTEMENT 3 points faibles spécifiques
    4. "verdict_court" : 1 phrase concise (max 20 mots)
    5. "recommandations" : EXACTEMENT 3 recommandations actionnables pour améliorer le CV

    CONTEXTE DE L'OFFRE :
    {offre_text}

    CV À ÉVALUER :
    {cv}
    """


# ---------------------------------------------------
# 3. Extraction des expériences
# ---------------------------------------------------
def prompt_extraire_experiences(texte_cv):
    cv = _truncate(texte_cv, MAX_CV_CHARS)
    return f"""
    Extrait les expériences du CV et renvoie UNIQUEMENT ce JSON strict :
    {{ "experiences": [{{"poste":"", "employeur":""}}] }}

    Si aucune info trouvée, renvoie : {{ "experiences": [] }}

    CV :
    {cv}
    """


# ---------------------------------------------------
# 4. Suggestions alternatives
# ---------------------------------------------------
def prompt_suggerer_alternatives(texte_cv):
    cv = _truncate(texte_cv, MAX_CV_CHARS)
    return f"""
    À partir du CV, suggère 3 postes/secteurs plus adaptés.
    RENVOIE UNIQUEMENT le JSON suivant :
    {{ "alternatives": ["", "", ""] }}

    CV :
    {cv}
    """


# ---------------------------------------------------
# 5. Génération du CV optimisé (JSON template compact)
# ---------------------------------------------------
def prompt_generer_cv_optimise(texte_cv, liste_exp, analyse_offre, contexte_rag, recos):
    return f"""
    Tu es un expert en rédaction de CV. Reformule le CV pour correspondre parfaitement à l'offre.
    Ta réponse DOIT être UNIQUEMENT un objet JSON valide respectant STRICTEMENT cette structure :

    {{
    "cv_optimise_complet": {{
        "entete": {{
        "prenom_nom": "Prénom Nom",
        "contact_info": "Adresse | Téléphone | Email | LinkedIn"
        }},
        "resume": "Un résumé exécutif percutant de 3-4 lignes.",
        "experiences": [
        {{
            "poste": "Titre du poste",
            "entreprise": "Nom Entreprise",
            "dates": "Dates (ex: Jan 2020 - Présent)",
            "taches": ["Action 1 + résultat", "Action 2 (mots-clés ATS)", "Action 3"]
        }}
        ],
        "formation": [
        {{
            "diplome": "Titre du diplôme",
            "ecole": "Nom École",
            "dates": "Année",
            "details": "Mention ou projet clé"
        }}
        ],
        "competences_techniques": "Liste des compétences techniques (Hard Skills) originales",
        "soft_skills": "Liste des compétences comportementales (Soft Skills) clés (ex: Communication, Rigueur...)", 
        "langues": "Langues et niveaux",
        "certifications": "Certifications obtenues",
        "interets": "Centres d'intérêt"
    }},
    "competences_suggerees": ["Compétence 1 (Absente du CV original)", "Compétence 2 (Absente du CV original)"]
    }}

    CONSIGNES :
    - Le champ 'soft_skills' doit mettre en avant les qualités humaines pertinentes pour le poste.
    - Le champ 'competences_techniques' ne contient que les Hard Skills.
    - Inspire-toi du style : {contexte_rag}
    - Applique les recos : {', '.join(recos)}

    OFFRE : {analyse_offre}
    CV ORIGINAL : {texte_cv}
    """

# ---------------------------------------------------
# 6. Modification d’un CV
# ---------------------------------------------------
def prompt_modification_cv(cv_actuel, instruction):
    cv = _truncate(cv_actuel, MAX_CV_CHARS)
    instr = instruction
    
    return f"""
    TU ES UN EXPERT EN RÉDACTION DE CV. 
    
    TÂCHE : Modifie le CV suivant selon l'instruction, mais RETOURNE LE CV COMPLET MODIFIÉ.
    
    RÈGLE ABSOLUE : Tu dois retourner TOUT LE CV, du début à la fin, avec les modifications intégrées.
    Ne retourne pas seulement les parties modifiées.
    
    INSTRUCTION DE MODIFICATION :
    {instr}
    
    CV ACTUEL COMPLET (conserve tout sauf les modifications demandées) :
    {cv}
    
    FORMAT DE RÉPONSE OBLIGATOIRE (JSON uniquement) :
    {{
      "cv_modifie": "LE CV MODIFIÉ COMPLET EN TEXTE (tout le CV du début à la fin)",
      "changements_faits": ["Description de la modification 1", "Description de la modification 2"]
    }}
    
    IMPORTANT : 
    1. Le champ "cv_modifie" doit contenir TOUT le CV, texte complet
    2. Conserve toutes les sections originales
    3. Applique seulement les modifications demandées
    4. Ne supprime rien sauf si explicitement demandé
    5. Le résultat doit être un CV complet et utilisable
    """

# ---------------------------------------------------
# 7. Comparaison des versions
# ---------------------------------------------------
def prompt_comparer_versions(cv_orig, cv_opt, analyse):
    o1 = _truncate(cv_orig, MAX_CV_CHARS)
    o2 = _truncate(cv_opt, MAX_CV_CHARS)
    ao = analyse if isinstance(analyse, str) else json.dumps(analyse)

    return f"""
    Compare les deux CV et liste 4 à 6 modifications concrètes.
    RENVOIE UNIQUEMENT UN JSON :
    {{ "modifications_apportes": [] }}

    OFFRE :
    {ao}

    CV_ORIGINAL :
    {o1}

    CV_OPTIMISE :
    {o2}
 """

# ==========================
# LOGIQUE PRINCIPALE (PHASES)
# ==========================

def validate_evaluation_json(eval_dict):
    """Valide et corrige le format du JSON d'évaluation"""
    if not isinstance(eval_dict, dict):
        return {"score": 0, "points_forts": [], "points_faibles": [], 
                "verdict_court": "Format invalide", "recommandations": []}
    
    # S'assurer que les clés existent
    result = {
        "score": int(eval_dict.get("score", 0)),
        "points_forts": list(eval_dict.get("points_forts", []))[:3],
        "points_faibles": list(eval_dict.get("points_faibles", []))[:3],
        "verdict_court": str(eval_dict.get("verdict_court", "Évaluation non disponible")),
        "recommandations": list(eval_dict.get("recommandations", eval_dict.get("recommendations", [])))[:3]
    }
    
    # S'assurer qu'on a exactement 3 éléments
    while len(result["points_forts"]) < 3:
        result["points_forts"].append("")
    while len(result["points_faibles"]) < 3:
        result["points_faibles"].append("")
    while len(result["recommandations"]) < 3:
        result["recommandations"].append("")
    
    return result

def phase_1_analyse(cv_bytes, cv_name, url_offre, session_id):
    """Phase 1 : Analyse. SAUVEGARDE TOUT SUR DISQUE."""
    if cv_name.endswith(".pdf"): 
        cv_text = extraire_texte_pdf(cv_bytes)
    else: 
        cv_text = extraire_texte_docx(cv_bytes)
    
    # 1. Sauvegarde Texte CV
    cv_text_path = save_text_to_disk(cv_text, session_id, "cv_original")
    
    # 2. Scraping Offre
    offre_text = extraire_offre_depuis_url(url_offre)
    
    # 3. Appels IA & Sauvegardes
    analyse_offre = safe_json_load(appeler_mistral(prompt_analyse_offre(offre_text))) or {}
    analyse_path = save_json_to_disk(analyse_offre, session_id, "analyse_offre")
    
    # Évaluation avec validation
    eval_raw = appeler_mistral(prompt_evaluer_cv(cv_text, analyse_offre))
    eval_parsed = safe_json_load(eval_raw)
    eval_orig = validate_evaluation_json(eval_parsed or {})
    eval_path = save_json_to_disk(eval_orig, session_id, "evaluation_original")
    
    # Extraction expériences
    
    exp_json = safe_json_load(appeler_mistral(prompt_extraire_experiences(cv_text)))
    exps = exp_json.get('experiences', []) if isinstance(exp_json, dict) else []
    exps_readable = [f"{e.get('poste')} @ {e.get('employeur')}" for e in exps]
    exps_path = save_json_to_disk(exps_readable, session_id, "experiences_list")

    # On ne retourne QUE des chemins (session légère)
    return {
        'cv_text_path': cv_text_path, 
        'analyse_offre_path': analyse_path,
        'evaluation_original_path': eval_path,
        'experiences_path': exps_path,
        'url_offre': url_offre,
        'score_initial': eval_orig.get('score', 0)
    }

def phase_2_optimisation(data, session_id):
    """Phase 2 : Optimisation & Sauvegarde disque - VERSION ROBUSTE"""
    # Chargement des données du disque
    cv_text = get_large_text_from_disk(data.get('cv_text_path'))
    analyse_offre = get_json_from_disk(data.get('analyse_offre_path'))
    eval_orig = get_json_from_disk(data.get('evaluation_original_path'))
    exps_readable = get_json_from_disk(data.get('experiences_path'))

    if not cv_text:
        raise Exception("CV original introuvable sur disque.")

    # Récupération des recommandations avec fallback
    recos = []
    if isinstance(eval_orig, dict) and 'recommandations' in eval_orig:
        recos = eval_orig['recommandations']
    elif isinstance(eval_orig, dict) and 'recommendations' in eval_orig:  # Alternative spelling
        recos = eval_orig['recommendations']
    
    # Limiter à 3 recommandations maximum
    if isinstance(recos, list):
        recos = recos[:3]
    else:
        recos = []

    # RAG avec gestion d'erreur
    try:
        rag = rag_retrieval_sbbert(cv_text, analyse_offre, "Tous_les_CVs")
    except Exception as e:
        print(f"[WARNING] RAG échoué: {e}")
        rag = ""

    # Appel Mistral avec prompt robuste
    raw = appeler_mistral(prompt_generer_cv_optimise(cv_text, exps_readable, analyse_offre, rag, recos))
    js = safe_json_load(raw)

    if js:
        # Extraire le CV optimisé selon la structure attendue
        if 'cv_optimise_complet' in js:
            cv_base = js['cv_optimise_complet']
            comp_sugg = js.get('competences_suggerees', [])
        else:
            cv_base = js
            comp_sugg = []

        # Sauvegarder JSON optimisé
        json_path = save_json_to_disk(cv_base, session_id, "cv_optimise_json")
        data['optimized_cv_json_path'] = json_path
        
        # Créer version texte lisible
        txt_ver = json_cv_to_text(cv_base)
        txt_path = save_text_to_disk(txt_ver, session_id, "cv_optimise_text")
        data['optimized_cv_path'] = txt_path
        data['competences_suggerees'] = comp_sugg
    else:
        # Fallback : sauvegarder la réponse brute comme texte
        print(f"[WARNING] JSON parsing failed, using raw text. Raw: {raw[:200]}...")
        txt_path = save_text_to_disk(raw, session_id, "cv_optimise_text")
        data['optimized_cv_path'] = txt_path
        data['optimized_cv_json_path'] = None
        data['competences_suggerees'] = []

    return data

def phase_alternatives(cv_text):
    return appeler_mistral(prompt_suggerer_alternatives(cv_text))
# ==========================
# FONCTION PONT (Pour compatibilité main.py)
# ==========================
def processing(cv_text, job_description=""):
    """
    Fonction wrapper qui connecte l'ancien main.py au nouveau moteur logique.
    """
    print(f"DEBUG: Processing appelé avec {len(cv_text)} caractères")
    
    try:
        # 1. Analyse de l'offre (si présente)
        analyse = {}
        if job_description:
            print("DEBUG: Analyse de l'offre en cours...")
            raw_analyse = appeler_mistral(prompt_analyse_offre(job_description))
            analyse = safe_json_load(raw_analyse) or {}

        # 2. Extraction rapide des expériences (pour le contexte)
        print("DEBUG: Extraction expériences...")
        raw_exps = appeler_mistral(prompt_extraire_experiences(cv_text))
        exp_json = safe_json_load(raw_exps)
        exps_list = []
        if exp_json and 'experiences' in exp_json:
             exps_list = [f"{e.get('poste', '')} @ {e.get('employeur', '')}" for e in exp_json['experiences']]

        # 3. Génération du CV Optimisé
        print("DEBUG: Génération du CV optimisé...")
        # On utilise des valeurs par défaut pour RAG et Recos pour ce mode rapide
        prompt_final = prompt_generer_cv_optimise(
            cv_text, 
            exps_list, 
            analyse, 
            contexte_rag="Standard", 
            recos=[]
        )
        
        resultat_mistral = appeler_mistral(prompt_final)
        
        # 4. Conversion en texte propre pour l'affichage
        json_result = safe_json_load(resultat_mistral)
        if json_result:
            return json_cv_to_text(json_result)
        
        return resultat_mistral

    except Exception as e:
        print(f"ERREUR DANS PROCESSING: {e}")
        return f"Une erreur est survenue : {str(e)}"
