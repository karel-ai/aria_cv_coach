#  Aria CV Coach

![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Mistral AI](https://img.shields.io/badge/AI-Mistral_Large-orange?style=for-the-badge)

**Aria CV Coach** est un agent IA autonome conçu pour optimiser les CVs en fonction d'offres d'emploi spécifiques. 
Il utilise une architecture **RAG (Retrieval-Augmented Generation)** et le modèle **Mistral AI** pour analyser, diagnostiquer et réécrire les CVs afin de maximiser leur impact et leur compatibilité ATS.

---

##  Fonctionnalités Clés

1.  ** Analyse Contextuelle** : Upload de CV (PDF/DOCX) et analyse sémantique de l'offre d'emploi (URL ou texte).
2.  ** Diagnostic IA** : Calcul d'un score de compatibilité (/100), identification des *Hard Skills* et *Soft Skills* manquants.
3.  ** Réécriture Intelligente** : Génération d'une version optimisée du CV, reformulée pour correspondre au ton et aux exigences du poste.
4.  ** Chatbot de Finition** : Interface de chat intégrée pour demander des modifications manuelles à l'IA (ex: "Rends le résumé plus punchy", "Ajoute mon niveau d'anglais").
5.  ** 100% Conteneurisé** : Déploiement facile et isolement total grâce à Docker.

---

##  Stack Technique

* **Backend :** Python, FastAPI, Uvicorn.
* **AI Engine :** Mistral AI API (`mistral-small-latest` / `mistral-large-latest`).
* **Traitement de Données :** PyPDF2, python-docx, BeautifulSoup4 (Scraping).
* **Frontend (SSR) :** Jinja2 Templates, HTML5, CSS3, Bootstrap.
* **Infrastructure :** Docker & Docker Compose.

---

##  Installation & Démarrage

### Pré-requis
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et lancé.
* Une clé API [Mistral AI](https://console.mistral.ai/) (Gratuite ou Payante).

### 1. Cloner le projet
```bash
git clone [https://github.com/votre-pseudo/aria-cv-coach.git](https://github.com/votre-pseudo/aria-cv-coach.git)
cd aria-cv-coach

```

Ton README est déjà très propre et bien structuré ! Pour l'étape 2, l'idée est de la rendre plus visuelle et sécurisée, tout en guidant l'utilisateur sur la provenance de la clé.

Voici une proposition de réécriture optimisée pour ton README :

---

### 2. Configuration des variables d'environnement

L'application nécessite une clé API Mistral pour fonctionner.

1. **Créez le fichier `.env`** à la racine du projet en copiant le modèle (ou en le créant manuellement) :
```bash
cp .env.example .env  # Si vous avez un fichier exemple, sinon : touch .env

```


2. **Ajoutez votre clé API** dans le fichier `.env` :
```env
# aria-cv-coach/.env
MISTRAL_API_KEY=votre_cle_api_ici_xyz

```



> [!IMPORTANT]
> Ne partagez jamais votre fichier `.env`. Il est déjà listé dans le `.gitignore` pour éviter toute publication accidentelle sur GitHub.
> Vous pouvez obtenir une clé gratuite sur la [Console Mistral AI](https://console.mistral.ai/).

---


### 3. Lancer l'application avec Docker

```bash
docker-compose up --build

```

*Le premier lancement peut prendre quelques minutes le temps de télécharger les images.*

### 4. Accéder à l'application

Ouvrez votre navigateur à l'adresse :
👉 **http://localhost:8000**

---

## 📂 Structure du Projet

```text
aria-cv-coach/
├── backend/
│   ├── app/
│   │   ├── static/
│   │   │   └── style.css            # Styles CSS (Design Glassmorphism)
│   │   ├── templates/               # Vues HTML (Jinja2)
│   │   │   ├── base.html            # Layout principal
│   │   │   ├── step1_upload.html    # Upload CV & Offre
│   │   │   ├── step2_diagnostic.html # Analyse & Score
│   │   │   ├── step3_optimize.html  # Réécriture IA
│   │   │   ├── step4_alternatives.html # Pistes de carrière
│   │   │   └── step5_final.html     # Chatbot & Résultats
│   │   ├── __init__.py
│   │   ├── export_cv.py             # Génération de documents (Stub/Impl)
│   │   ├── logic.py                 # Cerveau de l'IA (Mistral + Prompts)
│   │   ├── main.py                  # Contrôleur Principal (FastAPI)
│   │   └── rag_reformulation_cv.py  # Moteur RAG (Retrieval)
│   ├── Dockerfile                   # Configuration Image Python
│   └── requirements.txt             # Dépendances (FastAPI, MistralAI, etc.)
├── .env                             # Modèle de configuration (sans clés)
├── .gitignore                       # Fichiers à exclure de Git
├── docker-compose.yml               # Orchestration des conteneurs
└── README.md                        # Documentation du projet

```

---

## 🔮 Améliorations Futures

* [ ] Génération de fichiers PDF finaux avec mise en page moderne (`reportlab`).
* [ ] Historique des CVs optimisés (Base de données SQLite/Postgres).
* [ ] Mode "Interview Coach" pour générer des questions d'entretien probables.

---

## 👤 Auteur

**Karel Elong & Hélène Capon** - *AI & Data Science Students @ Aivancity*

* [LinkedIn](https://www.linkedin.com/in/karel-elong)
* [GitHub](https://github.com/karel-ai)

---

*Projet réalisé dans le cadre d'un cours de conception d'agent IA.*

```

```
