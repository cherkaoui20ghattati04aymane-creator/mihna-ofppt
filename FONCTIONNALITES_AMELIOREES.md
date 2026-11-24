# Fonctionnalités ajoutées ou améliorées — version 2

## CV Builder (page « Créateur de CV »)
- **5 modèles** : Moderne (bandeau), Professionnel ATS, Élégant deux colonnes, Minimaliste, Classique centré — PDF A4, pagination automatique, numéro de page.
- **6 palettes professionnelles** : Bleu professionnel, Noir et blanc, Vert moderne, Bordeaux élégant, Gris minimaliste, Violet moderne.
- **5 couleurs personnalisables** (principale, secondaire, titres, éléments graphiques, fond des sections) avec sélecteur de couleur + saisie hexadécimale, retour à la palette par défaut, **alerte de contraste** si un titre devient illisible.
- Le texte du bandeau passe automatiquement en blanc ou en sombre selon la couleur choisie (contraste WCAG).
- Changer de modèle ou de couleurs **ne modifie jamais** les informations saisies.
- **Photo facultative** : case à cocher, upload (JPEG/PNG/WEBP, 4 Mo max), vérification serveur (format réel, dimensions 96–6000 px, anti-bombe de décompression), ré-encodage JPEG sans métadonnées, **recadrage** (zoom + position), **ronde ou carrée**, **taille** réglable (60–140 pt), suppression à tout moment. Le modèle ATS n’imprime pas la photo (le message l’explique). La photo n’est jamais envoyée à l’IA.
- Aperçu PDF en direct + aperçu texte accessible aux couleurs choisies.
- Les couleurs et la photo sont enregistrées dans la version chiffrée du CV.

## Assistant IA du CV (mêmes pages, propositions uniquement)
Analyse (score de complétude) · Correction orthographique · Amélioration des descriptions · Suggestions de compétences · Résumé professionnel · Détection des informations manquantes · Optimisation pour une offre.
Chaque proposition affiche « Actuel / Proposé » et ne s’applique qu’après **« Accepter »**, si le texte n’a pas changé entre-temps. Mode local par défaut ; Gemini après aperçu exact des données et consentement. Garde-fous Gemini : cible existante obligatoire, **aucun chiffre nouveau**, compétence ajoutée seulement si une citation du CV la prouve.

## Assistant carrière (nouvelle page)
Expliquer une offre · Aide à la candidature (date limite, canal, écarts, relance) · Lettre de motivation (brouillon modifiable, copie, .txt) · Préparation d’entretien (questions, méthode STAR, questions à poser) · Compétences à développer (tirées des offres actives les plus proches du CV). Accessible depuis chaque carte d’offre (« Expliquer / préparer »).

## Gemini (service centralisé)
`backend/services/gemini_service.py` : SDK officiel, clé uniquement via `GEMINI_API_KEY`, liste blanche de modèles, délai, limitation par minute, quota quotidien persistant, cache, erreurs traduites, journal sans contenu, bascule locale automatique. Utilisé par : chatbot, recherche IA, matching, extraction de profil, analyse et suggestions CV, lettre, entretien, compétences, explication d’offre, aide à la candidature.

## Matching
Vocabulaire étendu (~130 compétences : développement, data/IA, gestion, tourisme/hôtellerie, design, langues) avec synonymes ; **points forts**, **suggestions**, **détail chiffré** de chaque composante, libellé (« Très / Partiellement / Peu compatible ») ; ville déduite du texte quand elle manque (signalée) ; **17 fois plus rapide** sur 88 offres, croissance linéaire.

## Connecteurs Jawb.ma et Wadifa.info
Verrouillés tant qu’une autorisation écrite n’est pas référencée ; robots.txt vérifié à chaque collecte ; délai entre requêtes (et `Crawl-delay`) ; arrêt sur CAPTCHA, 401/403/429 ; aucune redirection hors site ; nettoyage, dates FR/AR/RFC normalisées, date limite seulement si elle est explicitement annoncée, URLs validées, doublons détectés, offres expirées marquées ; descriptions stockées seulement si leur republication est autorisée ; résultats en **revue humaine** avant import ; historique et journal ; planification par `scripts/run_scrapers.py`.

## Base de données, sécurité, performance
Index de performance (migration sauvegardée, aucune donnée modifiée) · lecture directe d’une offre par identifiant · pagination facultative des offres · jeton PDF lié à la session · application utilisable même sans Dash · dates de quota en UTC · `favicon` sans 404 · Pillow dans les dépendances.
