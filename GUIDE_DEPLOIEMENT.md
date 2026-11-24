# Guide de déploiement — Stages Marrakech AI v2

## 1. Règle d’or : aucune donnée privée en ligne
Ne jamais publier : `.env`, `auth_gateway/.env.auth`, `private/`, `database/stages_marrakech.db`, `backups/`, `auth_gateway/data/`, `data_raw/`, `data_clean/`, CV, candidatures. Le `.gitignore` les exclut déjà. La démonstration en ligne utilise **uniquement** `database/stages_marrakech_public_demo.db` (données synthétiques, marquées `synthetic_public_demo`) en **lecture seule**.

## 2. Mettre à jour GitHub (GitHub Desktop)
1. Copier le contenu de l’archive `STAGES_MARRAKECH_AI_V2.zip` dans votre dépôt local `Stages-Marrakech-AI` (remplacer les fichiers existants).
2. Dans GitHub Desktop, vérifier la liste des fichiers : **aucun** `.env`, `.db` privé, `private/`, `backups/` ne doit apparaître.
3. Résumé du commit : « v2 : CV Studio, Gemini centralisé, connecteurs Jawb/Wadifa, matching explicable ». Commit, puis *Push origin*.

## 3. Render (service existant, rien à recréer)
`render.yaml` est inchangé dans son principe : `pip install -r requirements-production.txt`, Gunicorn sur `backend.wsgi:app`, mode démo public.
1. Render redéploie automatiquement après le push (ou *Manual Deploy → Deploy latest commit*).
2. Vérifier `https://<votre-service>.onrender.com/health` → `{"status":"ok"}`.
3. Vérifier `/cv.html` (CV Studio, assistant IA local), `/assistant-carriere.html`, `/offres.html`.

En démonstration publique : écritures refusées, Gemini et connecteurs refusés, assistance IA **locale** autorisée, aucun mot de passe.

L’erreur historique « Base initiale entreprises/offres absente » ne se produit pas si la variable `DATABASE` de Render pointe vers `database/stages_marrakech_public_demo.db` (c’est le cas dans `render.yaml`) et que ce fichier est bien poussé (il est explicitement autorisé par `.gitignore`).

## 4. Variables d’environnement (Render ou serveur)
Reprendre `.env.example`. En production publique : `PUBLIC_DEMO_MODE=true`, `PUBLIC_DEMO_DATA_CONFIRMED=true`, `COOKIE_SECURE=true`, `TRUST_PROXY=true`, `TRUSTED_HOSTS=.onrender.com`, `GEMINI_ENABLED=false`. La clé Gemini, si un jour nécessaire, se saisit dans *Environment* de Render (jamais dans le dépôt).

## 5. Après déploiement
- Logs Render : aucun contenu d’utilisateur ni clé n’est journalisé (seulement tâche, statut, durée).
- En cas d’échec de build : vérifier la version Python (3.12) et `requirements-production.txt`.
