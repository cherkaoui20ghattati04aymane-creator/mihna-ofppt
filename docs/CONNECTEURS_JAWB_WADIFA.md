# Connecteurs Jawb.ma et Wadifa.info

## 1. Étude préalable (17 novembre 2026)

| Point | Jawb.ma | Wadifa.info |
|---|---|---|
| API / flux officiel | Flux RSS et JSON décrits par le guide API de Jawb (vérifié dans le projet les 6 et 9 nov. 2026, voir `GUIDE_SOURCES_AUTORISEES.md`) | **Non vérifié** : site inaccessible depuis l’environnement d’audit |
| Usage prévu par la source | Flux destiné à la page carrière de l’entreprise qui publie | Inconnu |
| Conditions d’utilisation | CGU : contenu protégé, reproduction/usage soumis à autorisation | **Non lues** (inaccessibles) |
| robots.txt | **Non relu aujourd’hui** (inaccessible) ; vérifié automatiquement à chaque collecte | **Non lu** ; vérifié automatiquement à chaque collecte |
| Structure réelle des pages | Non nécessaire : seul le flux RSS est lu | Non vérifiée : seul un flux RSS/Atom est accepté |
| Type d’offres | Emplois et stages (Maroc) | Principalement concours publics (étiquetés « Concours », jamais présentés comme stages) |
| Décision | **Verrouillé** jusqu’à autorisation écrite de Jawb (et/ou de l’employeur) | **Verrouillé** jusqu’à vérification des CGU, du flux et autorisation écrite |

Ce qui n’a **pas** été fait faute d’accès : lecture des CGU et du robots.txt du jour, test d’une requête réelle. Pour compléter l’étude : `.venv\Scripts\python.exe scripts\check_sources.py` (lecture seule du robots.txt) puis lecture manuelle des CGU.

## 2. Règles appliquées par le code (`backend/scrapers/`)
- **Aucune collecte sans** : référence d’autorisation écrite + droits de consultation automatique, de stockage et de réaffichage cochés + collecte externe globale activée (+ adresse de flux pour Wadifa).
- **robots.txt** lu à chaque collecte ; adresse interdite → arrêt. `Crawl-delay` respecté ; 5 s minimum entre requêtes (8 s pour Wadifa) ; 2 pages maximum par collecte.
- **Aucun contournement** : CAPTCHA détecté, 401/403/429, redirection hors du site → arrêt immédiat et journalisé.
- **Flux XML uniquement** (RSS/Atom) : aucune analyse de pages HTML.
- **Champs stockés** : titre, organisme, ville, type d’opportunité, date de publication, date limite (si annoncée explicitement), URL d’origine, source, date de collecte, statut de vérification. **Description** seulement si sa republication est autorisée (case dédiée) ; sinon lien vers l’annonce d’origine.
- **Jamais d’offre inventée** ; une offre dont la date limite est passée est importée avec le statut « expirée » et n’apparaît jamais comme active.

## 3. Qualité des données (`quality.py`)
Nettoyage HTML/espaces · dates ISO, RFC 822, JJ/MM/AAAA, « 3 mars 2026 », mois arabes (« 15 دجنبر 2026 ») · date limite seulement après un marqueur (« date limite », « délai », « آخر أجل »…) · villes FR/AR · URL HTTPS du site source uniquement · doublons (URL canonique ou titre+organisme+ville) · statut actif/expiré/inconnu.

## 4. Parcours
```
Centre de collecte → Connecteurs Jawb.ma et Wadifa.info → autorisation documentée → « Collecter vers la revue »
→ annonces en attente (staging) → décision ligne par ligne → import (confirmation des droits, sauvegarde automatique)
```
Historique : chaque collecte est une ligne de `collector_runs` (mode `scraper`) avec métadonnées (référence d’autorisation, robots.txt, champs stockés, rejets). Journal : `logs/scrapers.log` (sans contenu d’annonce).

## 5. Planification (Windows)
```
schtasks /Create /SC DAILY /ST 08:30 /TN "StagesMarrakech-Jawb" ^
  /TR "\"C:\chemin\PROJET_FINAL_AMELIORE\.venv\Scripts\python.exe\" \"C:\chemin\PROJET_FINAL_AMELIORE\scripts\run_scrapers.py\" --source jawb"
```
Le script n’importe rien : il dépose les annonces en revue. Code retour : 0 succès, 1 échec réseau/page, 2 connecteur bloqué.

## 6. API
| Méthode | Route | Rôle |
|---|---|---|
| GET | `/api/scrapers` | État, raisons de blocage |
| POST | `/api/scrapers/<jawb|wadifa>/config` | Autorisation, droits, flux, activation |
| POST | `/api/scrapers/<jawb|wadifa>/run` | Collecte vers le staging (403 si non autorisé) |
| POST | `/api/collect/runs/<id>/import` | Import après revue (`rights_confirmed: true`) |
