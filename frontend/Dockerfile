# Utilisation d'une version Node stable (LTS)
FROM node:18-alpine

WORKDIR /app

# Copie des fichiers de dépendances
COPY package*.json ./

# Installation des dépendances
RUN npm install

# Copie du reste du projet
COPY . .

# On expose le port 3000
EXPOSE 3000

# Commande de développement (passer à 'npm run start' après un 'npm run build' pour la prod)
CMD ["npm", "run", "dev"]