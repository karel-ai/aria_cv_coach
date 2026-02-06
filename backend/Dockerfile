# On fixe la version précise comme demandé
FROM python:3.10.19-slim

# Pour éviter que Python n'écrive des fichiers .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Pour que les logs s'affichent en temps réel
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Installation des dépendances système si nécessaire (ex: pour compiler certaines libs)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copie et installation des requirements
# Assurez-vous d'avoir fastapi, uvicorn, python-multipart, et openai dans ce fichier
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY ./app ./app

# On expose le port 8000
EXPOSE 8000

# Lancement avec Uvicorn (Serveur ASGI performant pour la prod)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]