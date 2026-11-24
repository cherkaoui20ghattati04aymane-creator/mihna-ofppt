# Référence HTTP de Mihna

Routes Flask déclarées dans les sources de la remise. Les lignes indiquent les paramètres, réponses et accès SQL repérés dans le gestionnaire et dans ses principaux utilitaires locaux. Les schémas JSON complets et les branches dynamiques se lisent dans le gestionnaire lié. Un tiret indique qu’aucun élément de ce type n’a été relevé statiquement.

## Authentification et erreurs communes

- En mode local avec passerelle, les API métier exigent une session authentifiée. Les mutations requièrent le jeton CSRF de la session. Les lectures et écritures sont résolues dans l’espace SQLite du compte. Les routes internes utilisent le canal de confiance de la passerelle.
- Le backend transforme une erreur de validation en HTTP 400 et une ressource absente en HTTP 404. Une session manquante renvoie HTTP 401, et les contrôles d’origine, de jeton ou de mode lecture seule peuvent renvoyer HTTP 403. Se reporter au code pour les contrats spécifiques aux services tiers.
- Dash enregistre aussi ses propres routes de mise en page, de dépendances et de callbacks sous `/analytics/`. Le navigateur les appelle via la même session. La route Flask de secours renvoie une page de diagnostic lorsque Dash est indisponible.

## Routes enregistrées par Dash

Vérifiées sur la carte Flask de l’application de démonstration. La passerelle protège les requêtes sur la version avec comptes. La disposition affiche les données issues de l’espace actif.

| Méthode et chemin | Usage et réponse |
|---|---|
| GET `/analytics/` et `/analytics/<path:path>` | Sert la page Dash et l’enveloppe de navigation. |
| GET `/analytics/_dash-layout` | Renvoie la disposition JSON des composants. |
| GET `/analytics/_dash-dependencies` | Renvoie le graphe JSON des entrées, sorties et états des callbacks. |
| POST `/analytics/_dash-update-component` | Reçoit la cible et les valeurs de composants dans une requête JSON Dash, puis renvoie les propriétés calculées. Les callbacks métier utilisent les données de l’espace actif. |
| GET `/analytics/_dash-component-suites/<string:package_name>/<path:fingerprinted_path>` | Sert les scripts et styles fournis par les composants Dash. |
| GET `/analytics/assets/<path:filename>` | Sert un fichier du répertoire des ressources de Dash. |
| GET `/analytics/_favicon.ico` | Sert l’icône de Dash. |
| GET `/analytics/_reload-hash` | Renvoie les métadonnées de rechargement du client Dash. |

## Backend Flask · `backend/ai_routes.py`

### GET `/api/ai/status`

- Gestionnaire [ai_status](../backend/ai_routes.py#L71). Écran ou fonction concernée **Gemini / paramètres**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `career_tasks`, `cv_actions`, `gemini_cv_actions`, `local_available`, `privacy`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### POST `/api/ai/verify`

- Gestionnaire [ai_verify](../backend/ai_routes.py#L78). Écran ou fonction concernée **Gemini / paramètres**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `erreur`, `result`, `status`. Branches HTTP et exceptions explicites `403`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET `/api/cvs/design-options`

- Gestionnaire [design_options](../backend/ai_routes.py#L89). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `color_keys`, `color_labels`, `palettes`, `photo`, `templates`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### POST `/api/cvs/design/check`

- Gestionnaire [design_check](../backend/ai_routes.py#L97). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `design`, `warnings`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### POST `/api/cvs/photo`

- Gestionnaire [upload_photo](../backend/ai_routes.py#L103). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées fichiers `photo`.
- Réponse JSON. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### POST `/api/ai/cv/<action>/preview`

- Gestionnaire [cv_assist_preview](../backend/ai_routes.py#L129). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `action`.
- Réponse JSON avec `digest`, `note`, `payload`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_cv_request`, `_digest`.

### POST `/api/ai/cv/<action>`

- Gestionnaire [cv_assist](../backend/ai_routes.py#L137). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `action`.
- Réponse JSON avec `action`, `analysis`, `mode`, `notice`, `suggestions`. Branches HTTP et exceptions explicites `GeminiError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_cv_request`, `_gemini_ready`.

### POST `/api/ai/career/<task>/preview`

- Gestionnaire [career_preview](../backend/ai_routes.py#L181). Écran ou fonction concernée **Assistant carrière**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `task`.
- Réponse JSON avec `digest`, `note`, `payload`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_career_request`, `_digest`.

### POST `/api/ai/career/<task>`

- Gestionnaire [career](../backend/ai_routes.py#L189). Écran ou fonction concernée **Assistant carrière**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `task`.
- Réponse JSON avec `local`, `mode`, `notice`, `result`, `task`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_career_request`, `_gemini_ready`.

### POST `/api/ai/interview/feedback/preview`

- Gestionnaire [interview_feedback_preview](../backend/ai_routes.py#L223). Écran ou fonction concernée **Entretiens**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `digest`, `note`, `payload`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_digest`, `_interview_feedback_request`.

### POST `/api/ai/interview/feedback`

- Gestionnaire [interview_feedback_route](../backend/ai_routes.py#L231). Écran ou fonction concernée **Entretiens**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `fallback`, `feedback`, `mode`, `notice`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_gemini_ready`, `_interview_feedback_request`.

## Backend Flask · `backend/api.py`

### GET `/api/entreprises`

- Gestionnaire [get_companies](../backend/api.py#L186). Écran ou fonction concernée **Entreprises**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `entreprises`. Appels locaux repérés `companies`.

### GET `/api/offres`

- Gestionnaire [get_offers](../backend/api.py#L191). Écran ou fonction concernée **Offres / Fiche offre**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées requête `domain`, `kind`, `location`, `page`, `paid`, `per_page`, `subtype`.
- Réponse JSON. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `offres`. Appels locaux repérés `_enrich_offer`, `offers`.

### GET `/api/statistiques`

- Gestionnaire [statistics](../backend/api.py#L211). Écran ou fonction concernée **Statistiques**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `candidatures_par_statut`, `entreprises_avec_email`, `entreprises_avec_site`, `entreprises_par_secteur`, `offres_par_contrat`, `offres_par_stage`, `recent_offers`, `response_definition`, `response_rate`, `total_candidatures`, `total_entreprises`, `total_offres`, `total_secteurs`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `candidatures`, `entreprises`, `offres`. Appels locaux repérés `_enrich_offer`, `companies`, `count`, `offers`.

### GET `/api/profile`

- Gestionnaire [get_profile](../backend/api.py#L247). Écran ou fonction concernée **Profil**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `profile`, `updated_at`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_stored_profile`.

### PUT `/api/profile`

- Gestionnaire [put_profile](../backend/api.py#L253). Écran ou fonction concernée **Profil**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `profile`, `updated_at`. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `user_profile`. Appels locaux repérés `body`.

### GET `/api/profile/cv-draft`

- Gestionnaire [profile_cv_draft](../backend/api.py#L265). Écran ou fonction concernée **Profil**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `data`, `notice`, `profile_updated_at`, `saved`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_stored_profile`.

### GET `/api/career/interviews`

- Gestionnaire [interview_history](../backend/api.py#L272). Écran ou fonction concernée **Entretiens**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `items`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `ai_interview_history`. Appels locaux repérés —.

### GET `/api/career/interview-drafts`

- Gestionnaire [interview_drafts](../backend/api.py#L304). Écran ou fonction concernée **Entretiens**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `items`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `ai_interview_history`. Appels locaux repérés —.

### PUT `/api/career/interview-drafts`

- Gestionnaire [save_interview_draft](../backend/api.py#L314). Écran ou fonction concernée **Entretiens**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `draft_id`.
- Réponse JSON avec `id`. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `ai_interview_history`. Appels locaux repérés `_interview_submission`, `_owned_interview_draft`, `body`.

### POST `/api/career/interviews`

- Gestionnaire [save_interview_history](../backend/api.py#L333). Écran ou fonction concernée **Entretiens**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `draft_id`, `feedback`.
- Réponse JSON avec `created_at`, `cv_id`, `id`, `offer_id`. Branches HTTP et exceptions explicites `201`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `ai_interview_history`. Appels locaux repérés `_interview_submission`, `_owned_interview_draft`, `body`.

### GET `/api/candidatures`

- Gestionnaire [get_applications](../backend/api.py#L351). Écran ou fonction concernée **Candidatures / Statistiques** · JavaScript `mihna-pages`.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `candidatures`. Appels locaux repérés —.

### POST `/api/candidatures`

- Gestionnaire [create_application](../backend/api.py#L356). Écran ou fonction concernée **Candidatures / Statistiques** · JavaScript `mihna-pages`.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `id`, `message`. Branches HTTP et exceptions explicites `201`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `body`.

### PUT, PATCH `/api/candidatures/<int:ident>`

- Gestionnaire [update_application](../backend/api.py#L364). Écran ou fonction concernée **Candidatures / Statistiques** · JavaScript `mihna-pages`.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident`.
- Réponse JSON avec `message`. Branches HTTP et exceptions explicites `LookupError`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `candidature_history`, `candidatures`. Appels locaux repérés `body`, `values`.

### DELETE `/api/candidatures/<int:ident>`

- Gestionnaire [delete_application](../backend/api.py#L379). Écran ou fonction concernée **Candidatures / Statistiques** · JavaScript `mihna-pages`.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident`.
- Réponse voir le gestionnaire et ses appels. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET `/api/candidatures/<int:ident>/history`

- Gestionnaire [history](../backend/api.py#L385). Écran ou fonction concernée **Candidatures / Statistiques** · JavaScript `mihna-pages`.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident`.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `candidature_history`. Appels locaux repérés —.

### GET `/api/attempts`

- Gestionnaire [attempts](../backend/api.py#L390). Écran ou fonction concernée **Candidatures**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `send_attempts`. Appels locaux repérés —.

### GET `/api/cvs`

- Gestionnaire [list_cvs](../backend/api.py#L395). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `cvs`. Appels locaux repérés —.

### POST `/api/cvs`

- Gestionnaire [save_cv](../backend/api.py#L400). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `data`, `name`, `template`.
- Réponse voir le gestionnaire et ses appels. Branches HTTP et exceptions explicites `201`, `LookupError`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `cvs`. Appels locaux repérés `_persist_original_cv`, `body`.

### PATCH `/api/cvs/<int:ident>`

- Gestionnaire [edit_cv](../backend/api.py#L405). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident` · JSON `data`, `name`, `template`.
- Réponse voir le gestionnaire et ses appels. Branches HTTP et exceptions explicites `201`, `LookupError`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `cvs`. Appels locaux repérés `_persist_original_cv`, `body`.

### GET `/api/cvs/tailored`

- Gestionnaire [list_tailored_cvs](../backend/api.py#L431). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `cvs`. Appels locaux repérés —.

### POST `/api/cvs/tailored/preview`

- Gestionnaire [preview_tailored_cv](../backend/api.py#L437). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `cv_id`, `offer_id`.
- Réponse JSON avec `mode`, `notice`, `saved`. Branches HTTP et exceptions explicites `LookupError`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `cvs`, `offres`. Appels locaux repérés `_enrich_offer`, `_require_original_source`, `_stored_profile`, `body`, `get_cv`, `get_offer`.

### POST `/api/cvs/tailored`

- Gestionnaire [create_tailored_cv](../backend/api.py#L557). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_save_tailored_cv`, `body`.

### PATCH `/api/cvs/<int:ident>/tailored`

- Gestionnaire [update_tailored_cv](../backend/api.py#L563). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident`.
- Réponse JSON. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_save_tailored_cv`, `body`.

### GET `/api/cvs/<int:ident>`

- Gestionnaire [read_cv](../backend/api.py#L568). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident`.
- Réponse JSON. Branches HTTP et exceptions explicites `LookupError`.
- Tables SQL directes ou repérées dans un utilitaire local `cvs`. Appels locaux repérés `get_cv`.

### DELETE `/api/cvs/<int:ident>`

- Gestionnaire [delete_cv](../backend/api.py#L573). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident`.
- Réponse JSON avec `message`. Branches HTTP et exceptions explicites `LookupError`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `candidatures`, `cvs`. Appels locaux repérés —.

### POST `/api/cvs/optimize`

- Gestionnaire [optimize_cv](../backend/api.py#L586). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `cv_id`, `offer_id`.
- Réponse JSON avec `disclaimer`, `evidence`, `matched`, `missing`, `offer`, `recommendations`, `summary_suggestion`. Branches HTTP et exceptions explicites `LookupError`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `cvs`, `offres`. Appels locaux repérés `_enrich_offer`, `body`, `get_cv`, `get_offer`.

### GET `/api/cvs/<int:ident>/pdf`

- Gestionnaire [cv_pdf](../backend/api.py#L639). Écran ou fonction concernée **Studio CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident` · requête `download`.
- Réponse fichier. Branches HTTP et exceptions explicites `LookupError`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `cvs`. Appels locaux repérés `get_cv`.

### POST `/api/cvs/preview`

- Gestionnaire [preview_cv](../backend/api.py#L648). Écran ou fonction concernée **Studio CV** · JavaScript `cv-studio`.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `data`, `template`.
- Réponse fichier. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `body`.

### POST `/api/cvs/export`

- Gestionnaire [prepare_pdf_export](../backend/api.py#L654). Écran ou fonction concernée **Studio CV** · JavaScript `cv-studio`, `ui`.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `data`, `template`.
- Réponse JSON avec `token`. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `body`.

### GET `/api/cvs/export/<token>`

- Gestionnaire [download_pdf_export](../backend/api.py#L670). Écran ou fonction concernée **Studio CV** · JavaScript `cv-studio`, `ui`.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `token`.
- Réponse fichier. Branches HTTP et exceptions explicites `LookupError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### POST `/api/profile/extract`

- Gestionnaire [extract_profile](../backend/api.py#L678). Écran ou fonction concernée **Profil**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées fichiers `cv`.
- Réponse JSON avec `message`, `profile`, `text`. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### POST `/api/profile/gemini/preview`

- Gestionnaire [profile_gemini_preview](../backend/api.py#L687). Écran ou fonction concernée **Profil**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `digest`, `text`. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `body`.

### POST `/api/profile/gemini`

- Gestionnaire [profile_gemini](../backend/api.py#L695). Écran ou fonction concernée **Profil**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `consent`, `digest`, `reviewed_text`.
- Réponse JSON avec `mode`, `notice`, `profile`. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `body`.

### POST `/api/matching/preview`

- Gestionnaire [matching_preview](../backend/api.py#L719). Écran ou fonction concernée **Matching**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `digest`, `payload`. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `offres`. Appels locaux repérés `_enrich_offer`, `body`, `offers`, `selection`.

### POST `/api/matching`

- Gestionnaire [matching](../backend/api.py#L725). Écran ou fonction concernée **Matching**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `consent`, `cv_id`, `digest`, `mode`.
- Réponse JSON avec `disclaimer`, `mode`, `notice`, `results`. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `activity_log`, `offres`. Appels locaux repérés `_enrich_offer`, `body`, `offers`, `selection`.

### GET `/api/offres/<int:ident>/application`

- Gestionnaire [application_context](../backend/api.py#L750). Écran ou fonction concernée **Offres / Fiche offre**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident`.
- Réponse JSON avec `channel`, `cvs`, `offer`. Branches HTTP et exceptions explicites `LookupError`.
- Tables SQL directes ou repérées dans un utilitaire local `entreprises`, `offres`. Appels locaux repérés `_enrich_offer`, `companies`, `get_offer`, `list_cvs`, `offers`.

### POST `/api/offres/<int:ident>/apply`

- Gestionnaire [apply](../backend/api.py#L763). Écran ou fonction concernée **Offres / Fiche offre**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident` · JSON `action`, `confirmed`, `cv_id`, `message`, `subject` · en-têtes `Idempotency-Key`.
- Réponse JSON avec `duplicate`, `id`, `message`. Branches HTTP et exceptions explicites `201`, `LookupError`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `candidature_history`, `candidatures`, `cvs`, `entreprises`, `offres`. Appels locaux repérés `_enrich_offer`, `body`, `companies`, `get_cv`, `get_offer`.

### POST `/api/envoyer-cv`

- Gestionnaire [send_company_cv](../backend/api.py#L808). Écran ou fonction concernée **Infrastructure / navigation**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `confirmed`, `cv_id`, `email`, `email_confirmed`, `entreprise_id`, `message`, `subject` · en-têtes `Idempotency-Key`.
- Réponse JSON. Branches HTTP et exceptions explicites `LookupError`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `cvs`, `entreprises`. Appels locaux repérés `body`, `companies`, `get_cv`.

### GET `/api/map`

- Gestionnaire [map_data](../backend/api.py#L831). Écran ou fonction concernée **Carte**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `browser_key`, `companies`, `maps_enabled`, `notice`, `verified`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `entreprises`. Appels locaux repérés `companies`.

### GET `/api/collect/summary`

- Gestionnaire [collect_summary](../backend/api.py#L842). Écran ou fonction concernée **Sources de données**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### POST `/api/collect/offers/file/preview`

- Gestionnaire [collect_provided_offers_preview](../backend/api.py#L847). Écran ou fonction concernée **Sources de données**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées fichiers `file` · formulaire `consultation_allowed`, `display_allowed`, `mapping`, `permission_ref`, `source_name`, `storage_allowed`.
- Réponse JSON. Branches HTTP et exceptions explicites `201`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET, POST `/api/collect/settings`

- Gestionnaire [collect_settings](../backend/api.py#L862). Écran ou fonction concernée **Sources de données**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `career_feeds`, `career_import_approved`, `career_rights_confirmed`, `jawb_import_approved`, `jawb_permission_ref`, `rights_confirmed`.
- Réponse JSON. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `body`.

### GET, POST `/api/collect/runs`

- Gestionnaire [collect_runs](../backend/api.py#L885). Écran ou fonction concernée **Sources de données**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `id`, `mode`, `runs`, `status`, `summary`. Branches HTTP et exceptions explicites `202`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `body`.

### GET `/api/collect/runs/<int:ident>`

- Gestionnaire [collect_run_detail](../backend/api.py#L895). Écran ou fonction concernée **Sources de données**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident`.
- Réponse JSON. Branches HTTP et exceptions explicites `LookupError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### POST `/api/collect/runs/<int:ident>/staged/<int:stage_id>/decision`

- Gestionnaire [collect_stage_decision](../backend/api.py#L902). Écran ou fonction concernée **Sources de données**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident`, `int:stage_id` · JSON `decision`.
- Réponse JSON. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `body`.

### POST `/api/collect/runs/<int:ident>/import`

- Gestionnaire [collect_run_import](../backend/api.py#L908). Écran ou fonction concernée **Sources de données**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident` · JSON `rights_confirmed`, `sources`.
- Réponse JSON. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `collector_runs`, `gemini_search_history`. Appels locaux repérés `body`.

### GET `/api/ai-search/status`

- Gestionnaire [ai_search_status](../backend/api.py#L932). Écran ou fonction concernée **Recherche IA**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `gemini_search_history`. Appels locaux repérés `_ai_session_digest`.

### POST `/api/ai-search/local`

- Gestionnaire [ai_search_local](../backend/api.py#L950). Écran ou fonction concernée **Recherche IA**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `history_id`, `is_demo`, `mode`, `result`. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_ai_history`, `body`.

### POST `/api/ai-search/demo`

- Gestionnaire [ai_search_demo](../backend/api.py#L957). Écran ou fonction concernée **Recherche IA**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `candidates`, `history_id`, `is_demo`, `mode`, `workflow`. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_ai_history`, `body`.

### POST `/api/ai-search/gemini`

- Gestionnaire [ai_search_gemini](../backend/api.py#L970). Écran ou fonction concernée **Recherche IA**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `confirm_cost`.
- Réponse JSON avec `id`, `message`, `status`. Branches HTTP et exceptions explicites `202`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `gemini_search_history`. Appels locaux repérés `_ai_session_digest`, `_redacted_prompt`, `body`.

### GET `/api/ai-search/jobs/<ident>`

- Gestionnaire [ai_search_job](../backend/api.py#L996). Écran ou fonction concernée **Recherche IA**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `ident`.
- Réponse JSON avec `id`, `message`, `result`, `status`. Branches HTTP et exceptions explicites `LookupError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_ai_session_digest`.

### POST `/api/ai-search/jobs/<ident>/cancel`

- Gestionnaire [ai_search_cancel](../backend/api.py#L1003). Écran ou fonction concernée **Recherche IA**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `ident`.
- Réponse JSON avec `message`, `status`. Branches HTTP et exceptions explicites `LookupError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_ai_session_digest`.

### POST `/api/ai-search/jobs/<ident>/stage`

- Gestionnaire [ai_search_stage](../backend/api.py#L1012). Écran ou fonction concernée **Recherche IA**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `ident` · JSON `candidate_id`, `manual_verified`, `permission_ref`.
- Réponse JSON avec `id`, `offer`, `possible_duplicate`, `source`, `stage_id`, `status`. Branches HTTP et exceptions explicites `201`, `LookupError`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `collector_runs`, `collector_source_runs`, `collector_staging`, `gemini_search_history`. Appels locaux repérés `_ai_session_digest`, `_candidate_duplicate`, `body`.

### GET `/api/ai-search/history`

- Gestionnaire [ai_search_history](../backend/api.py#L1035). Écran ou fonction concernée **Recherche IA**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `items`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `gemini_search_history`. Appels locaux repérés `_ai_session_digest`.

### DELETE `/api/ai-search/history`

- Gestionnaire [ai_search_clear_history](../backend/api.py#L1040). Écran ou fonction concernée **Recherche IA**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `deleted`. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `gemini_search_history`. Appels locaux repérés `_ai_session_digest`, `body`.

### POST `/api/collect/companies/import`

- Gestionnaire [collect_companies_import](../backend/api.py#L1047). Écran ou fonction concernée **Sources de données**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées fichiers `file` · formulaire `apply`, `mapping`, `rights_confirmed`.
- Réponse JSON avec `mode`, `plan`, `result`. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET `/api/alerts/preferences`

- Gestionnaire [get_alert_preferences](../backend/api.py#L1065). Écran ou fonction concernée **Alertes**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### PUT `/api/alerts/preferences`

- Gestionnaire [put_alert_preferences](../backend/api.py#L1074). Écran ou fonction concernée **Alertes**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `email_consent`, `email_recipient`.
- Réponse JSON. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `alert_email_log`, `alert_preferences`. Appels locaux repérés `body`.

### GET `/api/alerts`

- Gestionnaire [get_alerts](../backend/api.py#L1105). Écran ou fonction concernée **Alertes**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `alert_email_log`, `alerts`, `offres`. Appels locaux repérés —.

### GET `/api/alerts/count`

- Gestionnaire [alert_count](../backend/api.py#L1114). Écran ou fonction concernée **Alertes**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `unread`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `alerts`. Appels locaux repérés —.

### POST `/api/alerts/<int:ident>/read`

- Gestionnaire [mark_alert_read](../backend/api.py#L1119). Écran ou fonction concernée **Alertes**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident`.
- Réponse JSON avec `ok`. Branches HTTP et exceptions explicites `LookupError`.
- Tables SQL directes ou repérées dans un utilitaire local `alerts`. Appels locaux repérés —.

### POST `/api/alerts/read-all`

- Gestionnaire [mark_alerts_read](../backend/api.py#L1127). Écran ou fonction concernée **Alertes**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `ok`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `alerts`. Appels locaux repérés —.

### DELETE `/api/alerts/<int:ident>`

- Gestionnaire [delete_alert](../backend/api.py#L1133). Écran ou fonction concernée **Alertes**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident`.
- Réponse voir le gestionnaire et ses appels. Branches HTTP et exceptions explicites `204`, `LookupError`.
- Tables SQL directes ou repérées dans un utilitaire local `alerts`. Appels locaux repérés —.

### GET `/api/assistant/history`

- Gestionnaire [assistant_history](../backend/api.py#L1162). Écran ou fonction concernée **Assistant carrière**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `messages`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `assistant_messages`. Appels locaux repérés —.

### GET `/api/assistant/status`

- Gestionnaire [assistant_status](../backend/api.py#L1172). Écran ou fonction concernée **Assistant carrière**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `gemini_available`, `label`, `local_available`, `model`, `reasons`, `remaining_today`, `state`, `verified`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### DELETE `/api/assistant/history`

- Gestionnaire [clear_assistant_history](../backend/api.py#L1181). Écran ou fonction concernée **Assistant carrière**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse voir le gestionnaire et ses appels. Branches HTTP et exceptions explicites `204`.
- Tables SQL directes ou repérées dans un utilitaire local `assistant_messages`. Appels locaux repérés —.

### POST `/api/assistant/preview`

- Gestionnaire [assistant_preview](../backend/api.py#L1195). Écran ou fonction concernée **Assistant carrière**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `question`.
- Réponse JSON avec `digest`, `local_result`, `mode`, `payload`, `summary`. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `assistant_preview_data`, `body`.

### POST `/api/assistant/chat`

- Gestionnaire [assistant_chat](../backend/api.py#L1202). Écran ou fonction concernée **Assistant carrière**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `consent`, `digest`, `mode`, `question`.
- Réponse JSON avec `mode`, `notice`. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local `assistant_messages`. Appels locaux repérés `assistant_preview_data`, `body`.

## Backend Flask · `backend/phase11_routes.py`

### GET `/api/saved-offers`

- Gestionnaire [list_saved](../backend/phase11_routes.py#L53). Écran ou fonction concernée **Offres sauvegardées**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `items`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `offres`, `saved_offers`. Appels locaux repérés `_db`.

### POST `/api/saved-offers`

- Gestionnaire [save_offer](../backend/phase11_routes.py#L65). Écran ou fonction concernée **Offres sauvegardées**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `note`, `offer_id`.
- Réponse JSON avec `duplicate`, `id`, `message`, `offer_id`. Branches HTTP et exceptions explicites `200`, `201`.
- Tables SQL directes ou repérées dans un utilitaire local `saved_offers`. Appels locaux repérés `_db`, `_int`.

### DELETE `/api/saved-offers/<int:offer_id>`

- Gestionnaire [unsave_offer](../backend/phase11_routes.py#L80). Écran ou fonction concernée **Offres sauvegardées**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:offer_id`.
- Réponse JSON avec `message`. Branches HTTP et exceptions explicites `LookupError`.
- Tables SQL directes ou repérées dans un utilitaire local `saved_offers`. Appels locaux repérés `_db`.

### GET `/api/saved-offers/ids`

- Gestionnaire [saved_ids](../backend/phase11_routes.py#L89). Écran ou fonction concernée **Offres sauvegardées**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `ids`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `saved_offers`. Appels locaux repérés `_db`.

### POST `/api/skills-gap`

- Gestionnaire [skills_gap_route](../backend/phase11_routes.py#L95). Écran ou fonction concernée **Compétences**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `cv_id`, `offer_id`.
- Réponse JSON. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_int`, `_latest_cv_id`, `_log`.

### POST `/api/cv-quality`

- Gestionnaire [cv_quality_route](../backend/phase11_routes.py#L110). Écran ou fonction concernée **Qualité du CV**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `cv`, `cv_id`, `offer_id`.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_int`, `_log`.

### GET `/api/roadmap`

- Gestionnaire [get_roadmap](../backend/phase11_routes.py#L184). Écran ou fonction concernée **Parcours**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_build_roadmap`.

### PUT `/api/roadmap`

- Gestionnaire [put_roadmap](../backend/phase11_routes.py#L189). Écran ou fonction concernée **Parcours**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `done`, `objective`, `step`.
- Réponse JSON. Branches HTTP et exceptions explicites `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_build_roadmap`, `_roadmap_state`, `_store_roadmap_state`.

### GET `/api/analytics/applications`

- Gestionnaire [applications_analytics](../backend/phase11_routes.py#L227). Écran ou fonction concernée **Statistiques**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `activity_log`, `candidature_history`, `candidatures`. Appels locaux repérés `_application_scores`, `_db`.

### GET `/api/candidatures/export.csv`

- Gestionnaire [export_applications_csv](../backend/phase11_routes.py#L244). Écran ou fonction concernée **Candidatures / Statistiques** · JavaScript `mihna-pages`.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse réponse HTTP. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `candidatures`. Appels locaux repérés `_db`.

### GET `/api/me/export`

- Gestionnaire [export_my_data](../backend/phase11_routes.py#L258). Écran ou fonction concernée **Paramètres** · JavaScript `mihna-pages`.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse réponse HTTP. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `activity_log`, `ai_interview_history`, `candidature_history`, `candidatures`, `cvs`, `saved_offers`. Appels locaux repérés `_db`, `_roadmap_state`.

### GET `/api/companies/lei`

- Gestionnaire [company_lei_route](../backend/phase11_routes.py#L284). Écran ou fonction concernée **Entreprises / Fiche entreprise**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées requête `q`.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET `/api/companies/overview`

- Gestionnaire [companies_overview_route](../backend/phase11_routes.py#L291). Écran ou fonction concernée **Entreprises / Fiche entreprise**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `offres`. Appels locaux repérés `_db`.

### GET `/api/companies/<int:ident>/insights`

- Gestionnaire [company_insights_route](../backend/phase11_routes.py#L296). Écran ou fonction concernée **Entreprises / Fiche entreprise**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `int:ident`.
- Réponse JSON. Branches HTTP et exceptions explicites `LookupError`.
- Tables SQL directes ou repérées dans un utilitaire local `entreprises`. Appels locaux repérés `_db`.

### GET `/api/career/interviews/<ident>`

- Gestionnaire [interview_detail](../backend/phase11_routes.py#L322). Écran ou fonction concernée **Entretiens**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `ident`.
- Réponse JSON. Branches HTTP et exceptions explicites `LookupError`.
- Tables SQL directes ou repérées dans un utilitaire local `ai_interview_history`. Appels locaux repérés `_db`, `_interview`.

### GET `/api/career/interviews-summary`

- Gestionnaire [interview_summary](../backend/phase11_routes.py#L330). Écran ou fonction concernée **Entretiens**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `items`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `ai_interview_history`. Appels locaux repérés `_db`, `_interview`.

### DELETE `/api/career/interviews/<ident>`

- Gestionnaire [interview_delete](../backend/phase11_routes.py#L337). Écran ou fonction concernée **Entretiens**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `ident`.
- Réponse JSON avec `message`. Branches HTTP et exceptions explicites `LookupError`.
- Tables SQL directes ou repérées dans un utilitaire local `ai_interview_history`. Appels locaux repérés `_db`.

### GET `/api/dashboard`

- Gestionnaire [dashboard](../backend/phase11_routes.py#L346). Écran ou fonction concernée **Tableau de bord**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `activity`, `applications`, `cvs`, `interviews`, `matching`, `profile`, `roadmap`, `saved`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `activity_log`, `ai_interview_history`, `candidatures`, `cvs`, `offres`, `saved_offers`. Appels locaux repérés `_build_roadmap`, `_db`.

### POST `/api/ai/feature/<feature>/preview`

- Gestionnaire [feature_preview](../backend/phase11_routes.py#L500). Écran ou fonction concernée **Gemini / paramètres**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `feature`.
- Réponse JSON avec `digest`, `gemini`, `notice`, `payload`. Branches HTTP et exceptions explicites `LookupError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_digest`, `_feature_payload`.

### POST `/api/ai/feature/<feature>`

- Gestionnaire [feature_run](../backend/phase11_routes.py#L511). Écran ou fonction concernée **Gemini / paramètres**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `feature` · JSON `consent`, `digest`.
- Réponse JSON avec `items`, `mode`, `model`, `notice`, `reasons`, `rejected`, `summary`. Branches HTTP et exceptions explicites `LookupError`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_digest`, `_feature_payload`, `_selected_summary`, `_validate_items`.

### GET `/api/ai/features`

- Gestionnaire [feature_list](../backend/phase11_routes.py#L543). Écran ou fonction concernée **Gemini / paramètres**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `features`, `gemini`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

## Backend Flask · `backend/scraper_routes.py`

### GET `/api/scrapers`

- Gestionnaire [scraper_status](../backend/scraper_routes.py#L12). Écran ou fonction concernée **Sources de données**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `policy`, `sources`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### POST `/api/scrapers/<source>/config`

- Gestionnaire [scraper_config](../backend/scraper_routes.py#L18). Écran ou fonction concernée **Sources de données**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `source`.
- Réponse JSON avec `sources`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### POST `/api/scrapers/<source>/run`

- Gestionnaire [scraper_run](../backend/scraper_routes.py#L24). Écran ou fonction concernée **Sources de données**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `source`.
- Réponse JSON avec `erreur`. Branches HTTP et exceptions explicites `403`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

## Backend Flask · `backend/web.py`

### GET `/api/auth/session`

- Gestionnaire [auth_session](../backend/web.py#L142). Écran ou fonction concernée **Session** · JavaScript `ui`.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `authenticated`, `configured`, `csrf`, `public_demo`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### POST `/api/auth/setup`

- Gestionnaire [setup](../backend/web.py#L152). Écran ou fonction concernée **Session**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `password`.
- Réponse JSON avec `csrf`, `erreur`. Branches HTTP et exceptions explicites `403`, `409`, `ValueError`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `setup`.

### POST `/api/auth/login`

- Gestionnaire [login](../backend/web.py#L169). Écran ou fonction concernée **Session**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées JSON `password`.
- Réponse JSON avec `csrf`, `erreur`. Branches HTTP et exceptions explicites `401`, `429`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `login`.

### POST `/api/auth/logout`

- Gestionnaire [logout](../backend/web.py#L184). Écran ou fonction concernée **Session**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `message`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### POST `/api/internal/gateway-session`

- Gestionnaire [internal_gateway_session](../backend/web.py#L189). Écran ou fonction concernée **Infrastructure / navigation**.
- Accès canal interne, contrôle de la boucle locale et du secret passerelle. Entrées relevées en-têtes `X-Internal-Gateway-Secret`.
- Réponse JSON avec `authenticated`, `configured`, `csrf`, `erreur`, `public_demo`. Branches HTTP et exceptions explicites `403`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET `/favicon.ico`

- Gestionnaire [favicon](../backend/web.py#L201). Écran ou fonction concernée **Infrastructure / navigation**.
- Accès point d’entrée public, selon le profil d’exécution. Entrées relevées —.
- Réponse voir le gestionnaire et ses appels. Branches HTTP et exceptions explicites `204`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET `/health`

- Gestionnaire [health](../backend/web.py#L205). Écran ou fonction concernée **Infrastructure / navigation**.
- Accès point d’entrée public, selon le profil d’exécution. Entrées relevées —.
- Réponse JSON avec `status`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET `/test-db`

- Gestionnaire [test_db](../backend/web.py#L209). Écran ou fonction concernée **Infrastructure / navigation**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `entreprises`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local `entreprises`. Appels locaux repérés —.

### GET `/`

- Gestionnaire [home](../backend/web.py#L214). Écran ou fonction concernée **Infrastructure / navigation**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse redirection. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET `/<path:filename>`

- Gestionnaire [frontend](../backend/web.py#L218). Écran ou fonction concernée **Infrastructure / navigation**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `path:filename`.
- Réponse JSON, fichier statique avec `erreur`. Branches HTTP et exceptions explicites `404`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET `/analytics/`

- Gestionnaire [analytics_unavailable](../backend/web.py#L260). Écran ou fonction concernée **Dash** · JavaScript `mihna-pages`, `ui`.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `erreur`. Branches HTTP et exceptions explicites `503`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

## Passerelle Flask · `auth_gateway/app.py`

### GET `/health`

- Gestionnaire [gateway_health](../auth_gateway/app.py#L196). Écran ou fonction concernée **Infrastructure / navigation**.
- Accès point d’entrée public, selon le profil d’exécution. Entrées relevées —.
- Réponse JSON avec `component`, `status`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET, POST `/login`

- Gestionnaire [gateway_login](../auth_gateway/app.py#L200). Écran ou fonction concernée **Connexion**.
- Accès point d’entrée public, selon le profil d’exécution. Entrées relevées formulaire `email`, `password`.
- Réponse redirection. Branches HTTP et exceptions explicites `400`, `401`, `403`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_attempt_key`, `auth_page`, `normalize_email`, `rotate_for`, `safe_next`.

### GET, POST `/register`

- Gestionnaire [gateway_register](../auth_gateway/app.py#L228). Écran ou fonction concernée **Inscription**.
- Accès point d’entrée public, selon le profil d’exécution. Entrées relevées formulaire `confirm_password`, `email`, `first_name`, `last_name`, `password`.
- Réponse redirection. Branches HTTP et exceptions explicites `400`, `403`, `409`, `429`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_attempt_key`, `auth_page`, `normalize_email`, `rotate_for`, `valid_name`.

### GET `/account`

- Gestionnaire [gateway_account](../auth_gateway/app.py#L267). Écran ou fonction concernée **Compte**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse voir le gestionnaire et ses appels. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `auth_page`.

### POST `/auth/logout`

- Gestionnaire [gateway_logout](../auth_gateway/app.py#L272). Écran ou fonction concernée **Session** · JavaScript `ui`.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse redirection. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET `/api/auth/session`

- Gestionnaire [gateway_auth_session](../auth_gateway/app.py#L282). Écran ou fonction concernée **Session** · JavaScript `ui`.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `authenticated`, `configured`, `csrf`, `gateway_profile`, `preference_scope`, `public_demo`. Branches HTTP et exceptions explicites —.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `_attempt_key`.

### POST `/api/auth/logout`

- Gestionnaire [gateway_api_logout](../auth_gateway/app.py#L290). Écran ou fonction concernée **Session**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées —.
- Réponse JSON avec `erreur`, `message`. Branches HTTP et exceptions explicites `403`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET, POST `/api/auth/login`

- Gestionnaire [block_legacy_auth](../auth_gateway/app.py#L303). Écran ou fonction concernée **Session**.
- Accès ancienne authentification bloquée par la passerelle. Entrées relevées —.
- Réponse JSON avec `erreur`. Branches HTTP et exceptions explicites `404`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET, POST `/api/auth/setup`

- Gestionnaire [block_legacy_auth](../auth_gateway/app.py#L303). Écran ou fonction concernée **Session**.
- Accès ancienne authentification bloquée par la passerelle. Entrées relevées —.
- Réponse JSON avec `erreur`. Branches HTTP et exceptions explicites `404`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés —.

### GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS `/`

- Gestionnaire [proxy_to_application](../auth_gateway/app.py#L308). Écran ou fonction concernée **Infrastructure / navigation**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées en-têtes `Origin`.
- Réponse JSON avec `erreur`. Branches HTTP et exceptions explicites `401`, `404`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `block_legacy_auth`, `gateway_api_logout`, `gateway_auth_session`.

### GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS `/<path:path>`

- Gestionnaire [proxy_to_application](../auth_gateway/app.py#L308). Écran ou fonction concernée **Infrastructure / navigation**.
- Accès session locale et CSRF sur mutation, selon les contrôles communs. Entrées relevées chemin `path:path` · en-têtes `Origin`.
- Réponse JSON avec `erreur`. Branches HTTP et exceptions explicites `401`, `404`.
- Tables SQL directes ou repérées dans un utilitaire local —. Appels locaux repérés `block_legacy_auth`, `gateway_api_logout`, `gateway_auth_session`.
