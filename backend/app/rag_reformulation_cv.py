# rag_reformulation_cv.py

import os
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT


"""
MODULE RAG SBERT pour optimiser la reformulation du CV.
Objectif : retourner des informations pertinentes de la base CV (sans LLM)
pour aider Mistral à mieux reformuler le CV final.
"""


# ======================
# Initialisation modèles
# ======================
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
kw_model = KeyBERT(model=sbert_model)


# =====================================
# Fonction principale appelée par Streamlit
# =====================================
def rag_retrieval_sbbert(cv_text_user, analyse_offre, base_cv_folder=r"Tous_les_CVs"):
    """
    Recherche les sections de CV les plus proches du CV utilisateur + offre.

    Parameters
    ----------
    cv_text_user : str
        Texte du CV de l'utilisateur
    analyse_offre : dict
        Analyse JSON de l’offre d’emploi provenant de optimizer_app
    base_cv_folder : str
        Dossier contenant les exemples de CV (base de connaissances)
        au format .txt ou .md

    Returns
    -------
    str : texte contextuel pour Mistral
    """

    # -----------------------------
    # 1. Charger les CV de la base
    # -----------------------------
    cv_paths = sorted(list(Path(base_cv_folder).glob("*.txt")))
    if not cv_paths:
        return "Aucune base CV trouvée pour le RAG."

    cv_texts = [Path(p).read_text(encoding="utf-8") for p in cv_paths]

    # -----------------------------
    # 2. Extraire keywords de l’offre
    # -----------------------------
    job_keywords = analyse_offre.get("competences_cles", []) + \
                   analyse_offre.get("mots_cles_ats", []) + \
                   analyse_offre.get("missions_principales", [])

    job_keywords_list = list(set(job_keywords))  # éviter doublons

    # -----------------------------
    # 3. Générer keywords pour chaque CV modèle
    # -----------------------------
    cv_keywords = []
    for text in cv_texts:
        kws = kw_model.extract_keywords(text, keyphrase_ngram_range=(1,2),
                                        stop_words='english', top_n=10)
        cv_keywords.append([kw[0] for kw in kws])

    # -----------------------------
    # 4. Embeddings SBERT
    # -----------------------------
    cv_kw_texts = [" ".join(kws) for kws in cv_keywords]
    cv_embeddings = sbert_model.encode(cv_kw_texts)

    job_emb = sbert_model.encode([" ".join(job_keywords_list)])[0]

    # -----------------------------
    # 5. Similarité
    # -----------------------------
    sims = cosine_similarity([job_emb], cv_embeddings)[0]
    ranked_idx = np.argsort(sims)[::-1]

    # -----------------------------
    # 6. Filtrer CVs pertinents
    # -----------------------------
    threshold = 0.40
    relevant_idx = [i for i, s in enumerate(sims) if s >= threshold]

    # Si aucun CV n'est pertinent → prendre le top 3 quand même
    if not relevant_idx:
        relevant_idx = ranked_idx[:3]

    # -----------------------------
    # 7. Clustering pour diversifier
    # -----------------------------
    relevant_embeddings = cv_embeddings[relevant_idx]
    k = min(3, len(relevant_embeddings))

    kmeans = KMeans(n_clusters=k, random_state=42).fit(relevant_embeddings)
    labels = kmeans.labels_

    # -----------------------------
    # 8. Sélectionner le meilleur CV par cluster
    # -----------------------------
    selected_texts = []

    for cluster_id in range(k):
        # indices appartenant au cluster
        cluster_members = [i for i, lab in zip(relevant_idx, labels) if lab == cluster_id]

        # choisir le plus similaire du cluster
        best_member = max(cluster_members, key=lambda i: sims[i])
        selected_texts.append(cv_texts[best_member])

    # -----------------------------
    # 9. Générer un contexte final structuré
    # -----------------------------
    final_context = "\n\n====================\n".join(selected_texts)

    return final_context
