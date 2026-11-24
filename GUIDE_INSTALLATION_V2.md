# Guide d’installation — Stages Marrakech AI v2 (Windows)

## Prérequis
- Windows 10/11, **Python 3.12** installé pour votre compte (`py -3.12 --version`).
- Connexion Internet pour la première installation des dépendances.

## Étapes (dossier amélioré `PROJET_FINAL_AMELIORE`)
1. **Copier vos données privées** depuis le projet original (rien n’est écrasé, l’original reste intact) :
   double-cliquez `COPIER_DONNEES_LOCALES.bat` (ou `COPIER_DONNEES_LOCALES.bat "C:\…\PROJET_FINAL"`).
   Il copie `.env`, `private\`, `database\stages_marrakech.db`, `data_clean\`, `data_raw\`, `auth_gateway\.env.auth`, `auth_gateway\data\`.
2. **Installer** : `INSTALLER_WINDOWS.bat` → crée `.venv` et installe `requirements.txt` (Flask, Dash, Plotly, ReportLab, Pillow, google-genai…).
3. **Vérifier** : `VERIFIER_INSTALLATION.bat`, puis `LANCER_TESTS.bat` (tous les tests doivent réussir, y compris Dash et SDK Gemini).
4. **Lancer** :
   - mode personnel : `LANCER_APPLICATION.bat` → http://127.0.0.1:5000
   - mode multi-utilisateur avec connexion : `LANCER_MON_PROJET.bat`
5. Au premier lancement en mode personnel, le navigateur demande de créer un mot de passe (12 caractères minimum).

Au premier démarrage, une **sauvegarde automatique** de la base est créée dans `backups\avant_phase10_index_*.db`, puis des index de performance sont ajoutés (aucune donnée modifiée).

## Gemini (facultatif)
Voir `docs\GEMINI.md`. En bref : renseigner `GEMINI_ENABLED=true`, `GEMINI_API_KEY=…`, `GEMINI_FREE_TIER_CONFIRMED=true` dans `.env`, redémarrer, puis `.venv\Scripts\python.exe scripts\test_gemini.py`.

## Connecteurs Jawb / Wadifa (facultatif)
Voir `docs\CONNECTEURS_JAWB_WADIFA.md`. Verrouillés tant qu’une autorisation écrite n’est pas référencée dans le Centre de collecte.

## Dépannage
| Symptôme | Solution |
|---|---|
| « Le module d’analyses Dash n’est pas installé » | Relancer `INSTALLER_WINDOWS.bat` |
| « Base initiale entreprises/offres absente » | `database\stages_marrakech.db` manquante : relancer `COPIER_DONNEES_LOCALES.bat` |
| Port 5000 occupé | Fermer l’autre fenêtre du serveur |
| Gemini « non activé » | Vérifier les trois variables de `.env`, puis `scripts\test_gemini.py` |
| Photo refusée | JPEG/PNG/WEBP, 4 Mo max, au moins 96 px de côté |
