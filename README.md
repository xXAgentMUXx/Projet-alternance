# Projet-alternance
# Job Search Dashboard

## Présentation

Job Search Dashboard est une application de recherche d'alternance permettant de centraliser les offres provenant de plusieurs plateformes.

Le projet est composé de deux parties :

- **Frontend** : React + Vite
- **Backend** : FastAPI

---

# Prérequis

Avant de lancer le projet, installer :

- Python 3.11 ou supérieur
- Node.js 20 ou supérieur
- npm
- Git

---

# Installation

## 1. Cloner le projet

```bash
git clone <url-du-projet>

cd Projet-alternance/projet-alternance
```

---

## 2. Installer les dépendances Python

Depuis le dossier **projet-alternance** :

```bash
pip install -r requirements.txt
```

---

## 3. Installer les dépendances du Frontend

Se placer dans le dossier :

```bash
cd frontend
```

Puis :

```bash
npm install
```

---

# Configuration

Créer un fichier `.env` dans le backend contenant les variables nécessaires.

Exemple :

```env
GEMINI_API_KEY=
LABONNEALTERNANCE_API_KEY=
```

Adapter les valeurs suivant votre environnement.

---

# Lancer le Backend

Depuis le dossier **projet-alternance** :

```bash
py -m uvicorn app:app --reload --port 8000
```

ou suivant votre structure :

```bash
py -m uvicorn main:app --reload --port 8000
```

Le backend sera disponible sur :

```
http://localhost:8000
```

---

# Lancer le Frontend

Depuis le dossier **frontend** :

```bash
npm run dev
```

Le frontend sera disponible sur :

```
http://localhost:5173
```

---

# Structure du projet

```
projet-alternance/

│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
│
├── scrappers/
│
├── json/
│
├── main.py
├── requirements.txt
├── .env
└── ...
```

---

# Fonctionnalités

- Recherche multi-plateformes
- Génération de lettres de motivation IA
- Gestion des candidatures
- Gestion des entreprises bloquées
- Notifications Discord
- Notifications Gmail
- Dashboard des candidatures
- Réseau professionnel
- Authentification JWT

---

# Technologies utilisées

## Frontend

- React
- Vite
- React Router
- TailwindCSS

## Backend

- FastAPI
- Uvicorn
- Python

## IA

- Gemini

## Déploiement

- Cloudflare Workers
- Render
- GitHub Actions

---

# Commandes utiles

### Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### Installer les dépendances React

```bash
npm install
```

### Lancer le backend

```bash
py -m uvicorn app:app --reload
```

ou

```bash
py -m uvicorn main:app --reload 
```

### Lancer le frontend

```bash
npm run dev
```

---

# Auteur

Mathys Urban

Projet Personnel et éducatif – Recherche d'alternance automatisée.
cepela9839@fixscal.com
