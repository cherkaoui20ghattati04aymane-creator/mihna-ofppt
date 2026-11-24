# Documentation Gemini — Stages Marrakech AI v2

## 1. Principe
Toutes les fonctions IA passent par **`backend/services/gemini_service.py`**. Chaque fonction a une version **locale** (toujours disponible, sans réseau). Gemini n’est utilisé que si l’administrateur l’a activé **et** si l’utilisateur a relu l’aperçu exact des données puis donné son accord.

Modèle par défaut : **`gemini-3.5-flash-lite`** (modèle stable de la documentation officielle `ai.google.dev/gemini-api/docs/models`, vérifiée le 17 novembre 2026). Liste blanche par défaut : `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.6-flash`, `gemini-3.8-flash`. SDK officiel : `google-genai` (déjà dans `requirements.txt`).

> État : **Gemini n’a pas été testé avec une vraie clé** (aucune clé fournie, réseau de l’environnement d’audit coupé). Le contrat SDK est testé avec des clients simulés. Faites le test réel avec `scripts\test_gemini.py`.

## 2. Activer Gemini (sur votre ordinateur)
1. Créez (ou régénérez) une clé dans Google AI Studio. **Si une clé a déjà été collée dans une conversation, un e-mail ou un dépôt, révoquez-la et créez-en une nouvelle.**
2. Ouvrez le fichier **`.env`** du projet (jamais `.env.example`, jamais le code) et renseignez :
   ```
   GEMINI_ENABLED=true
   GEMINI_API_KEY=collez_votre_cle_ici
   GEMINI_FREE_TIER_CONFIRMED=true
   GEMINI_MODEL=gemini-3.5-flash-lite
   ```
3. Double-cliquez **`TESTER_GEMINI.bat`** : il affiche la configuration lue (sans la clé), les modèles disponibles pour **votre** clé, puis le résultat d’une **vraie** requête (réussie/échouée, modèle, temps, type d’erreur).
4. Relancez l’application. Le journal de démarrage affiche : `Gemini au démarrage : activé=True, clé présente=True, modèle=…, SDK google-genai=True, prêt=True`.
5. Dans « Créateur de CV » → « Assistant IA du CV », cliquez **« Tester la connexion Gemini »** : le badge passe à « Gemini connecté — test réel réussi » **uniquement** si Google a répondu.

États affichés : « Gemini indisponible » (configuration incomplète, raisons listées) · « configuré — connexion non encore testée » · « connecté — test réel réussi » · « dernier test réel échoué : <type d’erreur> ». Aucun statut « connecté » n’est affiché sans test réel réussi.

Test pytest réel (facultatif) : `set RUN_GEMINI_REAL_TEST=1` puis `.venv\Scripts\python.exe -m pytest tests\test_gemini_real.py -q -s`.

Niveau gratuit : la page officielle des tarifs indique `gemini-3.5-flash-lite` « Free of charge » en niveau gratuit, avec utilisation des données pour améliorer les produits Google. L’application n’envoie jamais nom, email, téléphone, liens ni photo et demande votre accord avant chaque envoi.

## 3. Garde-fous

| Réglage `.env` | Défaut | Rôle |
|---|---|---|
| `GEMINI_TIMEOUT_SECONDS` | 20 | Délai maximal d’une requête |
| `GEMINI_RATE_PER_MINUTE` | 8 | Limitation : au-delà, bascule locale immédiate |
| `GEMINI_DAILY_LIMIT` | 200 | Quota quotidien local (compteur dans `private/gemini_usage.json`) |
| `GEMINI_CACHE_TTL_SECONDS` | 900 | Une demande identique n’est pas renvoyée à Gemini pendant 15 min |
| `GEMINI_ALLOWED_MODELS` | (vide) | Liste blanche personnalisée |

Erreurs traduites en messages clairs, avec bascule locale : clé absente ou valeur d’exemple, clé invalide (400 « API key not valid »/401/403), quota 429, modèle indisponible (404), délai dépassé, absence d’Internet (DNS/connexion), réponse vide ou invalide, SDK absent, Gemini désactivé.

**Journal** (`stages.gemini`) : nom de la tâche, modèle, statut, durée. Jamais le texte envoyé, la réponse ou la clé.

## 4. Confidentialité
Avant tout envoi : `POST …/preview` renvoie **exactement** les données transmises et leur empreinte SHA-256 ; l’appel réel exige `consent: true` + cette empreinte. Sont **toujours exclus** : nom, email, téléphone, liens LinkedIn/GitHub, photo. Emails, téléphones et liens présents dans les textes sont masqués (`[email retiré]`…). Mode démonstration publique : Gemini refusé.

## 5. Fonctionnalités et vérifications

| Fonction | Route | Vérification de la réponse Gemini |
|---|---|---|
| Chatbot | `/api/assistant/chat` | IDs d’offres limités à ceux transmis |
| Recherche de stages | `/api/ai-search/gemini` | Sources citées (grounding) obligatoires pour l’import |
| Matching CV/offre | `/api/matching` | Chaque rapprochement doit citer le texte exact de l’offre |
| Test de connexion réel | `POST /api/ai/verify` | Requête minimale sans donnée personnelle ; résultat sans clé |
| Analyse de CV (points forts/faibles) | `/api/ai/cv/analyze` | Aucun chiffre absent du CV, aucune coordonnée |
| Suggestions CV | `/api/ai/cv/<action>` | Cible existante, texte d’origine identique, **aucun chiffre nouveau**, aucun email/lien, compétence prouvée par une citation |
| Lettre de motivation | `/api/ai/career/cover_letter` | 200–4 000 caractères, aucune coordonnée générée |
| Préparation entretien | `/api/ai/career/interview` | Structure et longueurs contrôlées |
| Recommandations de compétences | `/api/ai/career/skills` | Compétence citée dans un extrait d’offre et absente du CV |
| Explication d’offre | `/api/ai/career/explain_offer` | Exigences conservées seulement si présentes dans l’offre |
| Assistance à la candidature | `/api/ai/career/application_help` | Étapes contrôlées, aucune coordonnée |
| Extraction de profil (PDF) | `/api/profile/gemini` | Compétences prouvées par citation |

Statut : `GET /api/ai/status` (activation, raisons, quota restant ; la clé n’apparaît jamais).

## 6. Utilisation dans le code
```python
from backend.services.gemini_service import GeminiService, GeminiError
service = GeminiService(config)
try:
    data = service.generate_json('ma_tache', payload, schema, instruction)
except GeminiError as exc:
    data = version_locale()          # message lisible : exc.user_message
```
