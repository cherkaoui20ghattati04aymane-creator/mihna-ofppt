# Inventaire du code Mihna

Index extrait des déclarations et décorateurs présents dans le code. Les routes des blueprints du backend sont indiquées avec leur préfixe applicatif lorsque celui-ci est déclaré dans le module. Les descriptions du fonctionnement des parcours figurent dans la documentation technique et l’index commenté des fonctionnalités.

## Fichiers

- `backend/__init__.py` · Application Stages Marrakech.
- `backend/ai_routes.py` · Routes de l'assistance IA (CV + carrière) et de la personnalisation du CV. · `_digest` (l. 27), `_draft_cv` (l. 31), `_offer` (l. 51), `_gemini_ready` (l. 62), `ai_status` (l. 71), `ai_verify` (l. 78), `design_options` (l. 89), `design_check` (l. 97), `upload_photo` (l. 103), `_cv_request` (l. 117), `cv_assist_preview` (l. 129), `cv_assist` (l. 137), `_career_request` (l. 169), `career_preview` (l. 181), `career` (l. 189), `_interview_feedback_request` (l. 214), `interview_feedback_preview` (l. 223), `interview_feedback_route` (l. 231)
- `backend/alert_mail.py` · Envoi facultatif d’alertes email, protégé par consentement et SMTP explicite. · `_send_queued` (l. 10), `deliver_new_alerts` (l. 58), `deliver_due_alert_emails` (l. 70)
- `backend/alerts.py` · Préférences et alertes d'offres explicables, dédupliquées et locales. · `preferences` (l. 8), `validate_preferences` (l. 17), `score_offer` (l. 31), `maybe_create_alert` (l. 62)
- `backend/analytics.py` · Véritable application Dash montée sur Flask, données relues à chaque callback. · `load_data` (l. 13), `figure_for` (l. 39), `missing_values` (l. 69), `dataset_notice` (l. 73), `quality_summary` (l. 84), `mount_dash` (l. 114)
- `backend/api.py` · `_ai_session_digest` (l. 32), `_redacted_prompt` (l. 39), `_ai_history` (l. 45), `_candidate_duplicate` (l. 54), `_grounded_worker` (l. 61), `config` (l. 91), `body` (l. 98), `companies` (l. 105), `_enrich_offer` (l. 109), `offers` (l. 154), `get_offer` (l. 162), `get_cv` (l. 170), `get_companies` (l. 186), `get_offers` (l. 191), `statistics` (l. 211), `_stored_profile` (l. 233), `get_profile` (l. 247), `put_profile` (l. 253), `profile_cv_draft` (l. 265), `interview_history` (l. 272), `_interview_submission` (l. 281), `_owned_interview_draft` (l. 295), `interview_drafts` (l. 304), `save_interview_draft` (l. 314), `save_interview_history` (l. 333), `get_applications` (l. 351), `create_application` (l. 356), `update_application` (l. 364), `delete_application` (l. 379), `history` (l. 385), `attempts` (l. 390), `list_cvs` (l. 395), `save_cv` (l. 400), `edit_cv` (l. 405), `_persist_original_cv` (l. 409), `list_tailored_cvs` (l. 431), `preview_tailored_cv` (l. 437), `_require_original_source` (l. 453), `_existing_identical_tailored` (l. 461), `_save_tailored_cv` (l. 477), `create_tailored_cv` (l. 557), `update_tailored_cv` (l. 563), `read_cv` (l. 568), `delete_cv` (l. 573), `optimize_cv` (l. 586), `cv_pdf` (l. 639), `preview_cv` (l. 648), `prepare_pdf_export` (l. 654), `download_pdf_export` (l. 670), `extract_profile` (l. 678), `profile_gemini_preview` (l. 687), `profile_gemini` (l. 695), `selection` (l. 706), `matching_preview` (l. 719), `matching` (l. 725), `application_context` (l. 750), `apply` (l. 763), `send_company_cv` (l. 808), `map_data` (l. 831), `collect_summary` (l. 842), `collect_provided_offers_preview` (l. 847), `collect_settings` (l. 862), `collect_runs` (l. 885), `collect_run_detail` (l. 895), `collect_stage_decision` (l. 902), `collect_run_import` (l. 908), `ai_search_status` (l. 932), `ai_search_local` (l. 950), `ai_search_demo` (l. 957), `ai_search_gemini` (l. 970), `ai_search_job` (l. 996), `ai_search_cancel` (l. 1003), `ai_search_stage` (l. 1012), `ai_search_history` (l. 1035), `ai_search_clear_history` (l. 1040), `collect_companies_import` (l. 1047), `get_alert_preferences` (l. 1065), `put_alert_preferences` (l. 1074), `get_alerts` (l. 1105), `alert_count` (l. 1114), `mark_alert_read` (l. 1119), `mark_alerts_read` (l. 1127), `delete_alert` (l. 1133), `assistant_cv_profile` (l. 1139), `assistant_history` (l. 1162), `assistant_status` (l. 1172), `clear_assistant_history` (l. 1181), `assistant_preview_data` (l. 1186), `assistant_preview` (l. 1195), `assistant_chat` (l. 1202)
- `backend/app.py` · Point d'entrée conservé : python backend/app.py.
- `backend/application_service.py` · Candidatures et SMTP : confirmation, provenance et idempotence persistante. · `insert_candidature` (l. 12), `resolve_channel` (l. 22), `send_cv` (l. 43)
- `backend/assistant.py` · Recherche locale contrôlée : aucune requête SQL n'est générée par un modèle. · `_latest_update` (l. 15), `_clean_offer` (l. 23), `_offer_rows` (l. 32), `retrieve` (l. 50), `gemini_payload` (l. 111), `gemini_answer` (l. 117)
- `backend/career_ai.py` · Assistant carrière : lettre de motivation, entretien, compétences, explication d'offre, aide à la candidature. · `_offer_text` (l. 20), `_clean` (l. 24), `_availability` (l. 29), `_first` (l. 38), `related_offers` (l. 42), `cover_letter` (l. 55), `interview` (l. 89), `skills_recommendations` (l. 125), `explain_offer` (l. 143), `application_help` (l. 162), `validate_interview_answers` (l. 220), `interview_feedback` (l. 232), `gemini_payload` (l. 254), `validate_interview_feedback` (l. 275), `validate_gemini` (l. 292), `run_local` (l. 343), `generated_at` (l. 357)
- `backend/career_features.py` · Phase 11 career features — deterministic, explainable, local rules. · `_split` (l. 64), `_sentences` (l. 68), `cv_text` (l. 72), `offer_text` (l. 80), `skills_gap` (l. 85), `_criterion` (l. 140), `cv_quality` (l. 145), `career_roadmap` (l. 253), `application_analytics` (l. 307), `_name_key` (l. 358), `company_insights` (l. 362), `companies_overview` (l. 391), `interview_assessment` (l. 403), `month_key` (l. 426), `today` (l. 433)
- `backend/collection_manager.py` · Tâches ponctuelles et ordonnanceur daemon limité à la vie du serveur Flask. · `_scheduler_log` (l. 17), `start_run` (l. 32), `ensure_scheduler` (l. 48), `collection_summary` (l. 97)
- `backend/collectors/__init__.py` · Connecteurs de collecte en lecture seule et imports SQLite non destructifs.
- `backend/collectors/catalog.py` · Registre des sources, licences et mesures d'exécution connues. · `_runtime_fields` (l. 152), `source_catalog` (l. 167)
- `backend/collectors/classification.py` · Classement explicable d'offres. Une absence d'indice reste une valeur inconnue. · `_text` (l. 7), `classify_offer` (l. 12), `filter_offer` (l. 79)
- `backend/collectors/companies.py` · Prévisualisation et import CSV/XLSX non destructif de fiches obtenues légalement. · `_norm` (l. 25), `normalize_sector` (l. 31), `parse_company_file` (l. 49), `company_plan` (l. 112), `import_companies` (l. 134)
- `backend/collectors/free_apis.py` · Narrow connectors for free APIs whose terms permit the intended use. · `_api_get` (l. 27), `_allowed_api_url` (l. 43), `parse_himalayas_payload` (l. 49), `fetch_himalayas` (l. 142), `deduplicate_records` (l. 185), `check_himalayas_job` (l. 199)
- `backend/collectors/gleif.py` · Import a bounded GLEIF LEI reference snapshot. This catalog is separate from employers. · `normalize` (l. 13), `_fold` (l. 33), `search` (l. 38), `main` (l. 52)
- `backend/collectors/jawb.py` · Connecteurs Jawb documentés. Les requêtes sont bornées et ne publient rien. · `_safe_jawb_url` (l. 17), `_request` (l. 23), `_local` (l. 36), `parse_rss` (l. 40), `fetch_rss` (l. 58), `fetch_company_feed` (l. 67), `fetch_career_rss` (l. 106), `_request_generic` (l. 123)
- `backend/collectors/jobicy.py` · Bounded synchronization of the documented free Jobicy jobs and status APIs. · `SourcePaused` (l. 20), `normalize` (l. 24), `status_map` (l. 51), `_request` (l. 58), `discover` (l. 70), `known_identities` (l. 87), `verify_statuses` (l. 95), `sync` (l. 105), `run_periodic` (l. 184)
- `backend/collectors/phase7_import.py` · Safe, explicit Phase 7 import of validated Himalayas records only. · `_sha256` (l. 17), `_https_himalayas` (l. 25), `load_and_validate` (l. 32), `preview_import` (l. 85), `backup_and_verify` (l. 132), `apply_import` (l. 148)
- `backend/collectors/platforms.py` · Connecteurs publics d'ATS. Les fonctions de parsing sont pures et testables hors réseau. · `_token` (l. 16), `_request` (l. 23), `parse_greenhouse` (l. 40), `fetch_greenhouse` (l. 59), `parse_lever` (l. 66), `fetch_lever` (l. 84), `parse_ashby` (l. 105), `fetch_ashby` (l. 131), `parse_smartrecruiters` (l. 138), `fetch_smartrecruiters` (l. 158)
- `backend/collectors/provided_offers.py` · Import d'offres à partir d'un fichier légalement transmis par un tiers. · `_header` (l. 31), `_rows` (l. 37), `parse_provided_offers` (l. 67), `stage_provided_file` (l. 120)
- `backend/collectors/schema.py` · Schéma canonique et validations de contenu public. · `clean_text` (l. 14), `canonical_url` (l. 21), `parse_date` (l. 39), `normalize_offer` (l. 62), `identity_key` (l. 116), `fingerprint` (l. 120), `content_hash` (l. 129)
- `backend/collectors/service.py` · Orchestrateur d'import public, incrémental, journalisé et jamais destructif. · `get_setting` (l. 14), `set_setting` (l. 24), `sources_config` (l. 30), `set_sources_config` (l. 48), `_connector_options` (l. 101), `create_run` (l. 129), `execute_run` (l. 139), `_existing_offer` (l. 208), `_exact_company` (l. 218), `_alert_match` (l. 225), `_offer_status` (l. 230), `import_run` (l. 236), `run_history` (l. 370), `run_details` (l. 374), `decide_staged_offer` (l. 405)
- `backend/config.py` · `_flag` (l. 7), `_text` (l. 12), `settings` (l. 16)
- `backend/cv_assistant.py` · Assistance au CV : propositions uniquement, jamais d'écriture automatique. · `_targets` (l. 47), `read_target` (l. 65), `_suggestion` (l. 78), `_advice` (l. 84), `_sentences` (l. 89), `_numbers` (l. 93), `cv_skills` (l. 97), `cv_text` (l. 102), `_keep_case` (l. 111), `fix_text` (l. 115), `grammar` (l. 130), `descriptions` (l. 147), `skills` (l. 172), `summary` (l. 206), `missing` (l. 229), `analyze` (l. 263), `optimize` (l. 281), `run_local` (l. 325), `anonymized_cv` (l. 342), `validate_analyze` (l. 373), `gemini_payload` (l. 407), `validate_gemini` (l. 417)
- `backend/cv_design.py` · Personnalisation du CV : modèles, palettes de couleurs et photo facultative. · `default_design` (l. 54), `validate_design` (l. 59), `luminance` (l. 78), `contrast_ratio` (l. 84), `readable_text_on` (l. 89), `mix` (l. 94), `contrast_warnings` (l. 101), `_decode_data_url` (l. 113), `_open_image` (l. 126), `_to_rgb` (l. 151), `_jpeg_data_url` (l. 163), `sanitize_upload` (l. 169), `normalize_photo` (l. 177), `photo_bytes` (l. 212)
- `backend/cv_pdf.py` · Rendu PDF A4 des modèles de CV (ReportLab). · `_fonts` (l. 33), `Photo` (l. 44), `Builder` (l. 79), `build_pdf` (l. 315)
- `backend/cv_service.py` · `validate_cv` (l. 13), `extract_pdf` (l. 53), `make_pdf` (l. 68)
- `backend/db.py` · Migrations additives, sauvegardées, sans remplacement de table métier. · `request_database` (l. 9), `request_backup_dir` (l. 20), `now` (l. 30), `backup_database` (l. 34), `connect` (l. 44), `migrate` (l. 58), `migrate_phase5` (l. 116), `migrate_phase7` (l. 214), `migrate_phase9` (l. 246), `rows` (l. 268), `migrate_phase10` (l. 273), `migrate_phase11` (l. 296), `migrate_phase12` (l. 313), `migrate_phase13` (l. 336), `migrate_phase14` (l. 373), `migrate_all` (l. 401)
- `backend/gemini_search.py` · Gemini Search Grounding, validation locale et simulation isolée. · `enabled_status` (l. 32), `_safe_public_https` (l. 45), `_get` (l. 63), `_safe_source_chunks` (l. 68), `_SearchSuggestionParser` (l. 78), `_grounding` (l. 95), `validate_criteria` (l. 114), `_search_prompt` (l. 134), `run_grounded_search` (l. 143), `simulate_demo_workflow` (l. 202)
- `backend/gemini_service.py` · SDK officiel ; données relues, consentement et activation obligatoires. · `anonymize` (l. 16), `payload` (l. 23), `validate_response` (l. 32), `generate_json` (l. 57), `interpret` (l. 67), `extract_profile` (l. 78)
- `backend/himalayas_refresh.py` · Keep the local Himalayas catalog current without deleting historical references. · `recently_verified` (l. 20), `status_url` (l. 29), `_due_offers` (l. 36), `refresh` (l. 43), `run_daily` (l. 93)
- `backend/matching.py` · Score déterministe et explicable : chaque composante et contribution sont retournées. · `norm` (l. 51), `tokens` (l. 55), `canonical` (l. 59), `_term_pattern` (l. 64), `has_term` (l. 68), `skills_from` (l. 72), `city_from` (l. 78), `local_profile` (l. 83), `validate_profile` (l. 87), `Corpus` (l. 102), `cosine` (l. 115), `score_label` (l. 125), `offer_skills` (l. 133), `rank` (l. 146)
- `backend/phase11_routes.py` · Phase 11 API: saved opportunities, skills gap, CV quality, career roadmap, · `_db` (l. 30), `_log` (l. 34), `_int` (l. 40), `_latest_cv_id` (l. 46), `list_saved` (l. 53), `save_offer` (l. 65), `unsave_offer` (l. 80), `saved_ids` (l. 89), `skills_gap_route` (l. 95), `cv_quality_route` (l. 110), `_roadmap_state` (l. 131), `_store_roadmap_state` (l. 141), `_facts` (l. 148), `_build_roadmap` (l. 163), `get_roadmap` (l. 184), `put_roadmap` (l. 189), `_application_scores` (l. 213), `applications_analytics` (l. 227), `export_applications_csv` (l. 244), `export_my_data` (l. 258), `company_lei_route` (l. 284), `companies_overview_route` (l. 291), `company_insights_route` (l. 296), `_interview` (l. 304), `interview_detail` (l. 322), `interview_summary` (l. 330), `interview_delete` (l. 337), `dashboard` (l. 346), `_digest` (l. 422), `_cv_for_ai` (l. 426), `_feature_payload` (l. 442), `_validate_items` (l. 475), `_selected_summary` (l. 490), `feature_preview` (l. 500), `feature_run` (l. 511), `feature_list` (l. 543)
- `backend/profile.py` · Validation and CV mapping for an account's encrypted professional profile. · `empty_profile` (l. 14), `validate_profile` (l. 28), `cv_draft` (l. 81)
- `backend/scraper_routes.py` · Routes des connecteurs Jawb.ma / Wadifa.info (configuration, état, collecte vers staging). · `scraper_status` (l. 12), `scraper_config` (l. 18), `scraper_run` (l. 24)
- `backend/scrapers/__init__.py` · Connecteurs d'offres externes conformes (Jawb.ma, Wadifa.info).
- `backend/scrapers/base.py` · Client HTTP poli : robots.txt, délai entre requêtes, domaine verrouillé, taille et délai bornés. · `ScraperError` (l. 18), `NotAuthorized` (l. 22), `RobotsDisallowed` (l. 26), `NetworkError` (l. 30), `PageUnavailable` (l. 34), `BlockedByProtection` (l. 38), `PoliteFetcher` (l. 43)
- `backend/scrapers/jawb_scraper.py` · Connecteur Jawb.ma — flux RSS public documenté par Jawb (aucun scraping HTML). · `feed_url` (l. 22), `collect` (l. 29)
- `backend/scrapers/pipeline.py` · Orchestration : autorisation → collecte → qualité → staging (revue humaine) → import existant. · `get_config` (l. 31), `set_config` (l. 41), `authorization_reasons` (l. 70), `status` (l. 80), `_offer_from` (l. 95), `run` (l. 105)
- `backend/scrapers/quality.py` · Qualité des données collectées : nettoyage, dates, URLs, doublons, statut. · `clean` (l. 30), `_fold` (l. 35), `normalize_date` (l. 39), `deadline_from` (l. 71), `city_from` (l. 81), `opportunity_type` (l. 89), `valid_url` (l. 102), `dedupe_key` (l. 115), `status_for` (l. 125), `parse_feed` (l. 131), `build_record` (l. 155), `deduplicate` (l. 182)
- `backend/scrapers/wadifa_scraper.py` · Connecteur Wadifa.info — flux RSS/Atom uniquement. · `collect` (l. 27)
- `backend/security.py` · `Vault` (l. 12)
- `backend/services/__init__.py` · Services réutilisables (IA, etc.).
- `backend/services/gemini_service.py` · Service Gemini centralisé. · `GeminiError` (l. 32), `GeminiDisabled` (l. 43), `GeminiRateLimited` (l. 48), `GeminiQuotaExceeded` (l. 53), `GeminiTimeout` (l. 58), `GeminiAuthError` (l. 63), `GeminiNetworkError` (l. 68), `GeminiModelUnavailable` (l. 73), `GeminiInvalidResponse` (l. 78), `_flag` (l. 97), `_int` (l. 101), `allowed_models` (l. 108), `GeminiService` (l. 117), `reset_state_for_tests` (l. 416), `service` (l. 423)
- `backend/tailoring.py` · Factual, local CV tailoring from a saved CV, account Profile, and one offer. · `_sentences` (l. 10), `_merge_entries` (l. 14), `_field_text` (l. 42), `_rank_entries` (l. 50), `_rank_skill_tokens` (l. 61), `_requirements` (l. 73), `build_tailored_cv` (l. 91)
- `backend/user_data.py` · Durable, per-account SQLite workspaces seeded without historical personal data. · `_account_key` (l. 25), `_user_lock` (l. 33), `_validate_existing_workspace` (l. 38), `_migrate_existing_workspace` (l. 49), `provision_user_database` (l. 64)
- `backend/validation.py` · `text` (l. 11), `email` (l. 17), `safe_url` (l. 24), `candidature` (l. 33)
- `backend/web.py` · `create_app` (l. 17)
- `backend/wsgi.py` · WSGI entry point used by production servers such as Gunicorn.
- `auth_gateway/__init__.py` · Authentification externe isolée pour Stages Marrakech AI.
- `auth_gateway/app.py` · `normalize_email` (l. 23), `valid_name` (l. 27), `safe_next` (l. 32), `_attempt_key` (l. 44), `create_app` (l. 48)
- `auth_gateway/config.py` · `_read_env_file` (l. 13), `_session_secret` (l. 26), `load_config` (l. 47)
- `auth_gateway/database.py` · `AuthStore` (l. 13)
- `auth_gateway/gunicorn.conf.py`
- `auth_gateway/launcher.py` · `QuietHandler` (l. 20), `port_free` (l. 25), `ensure_internal_secret` (l. 34), `check_database` (l. 54), `run_gateway_only` (l. 93), `main` (l. 104)
- `auth_gateway/ORIGINAL_SHA256_BEFORE.json`
- `auth_gateway/proxy.py` · `BackendTunnel` (l. 13)
- `auth_gateway/requirements-postgres.txt`
- `auth_gateway/requirements-production.txt`
- `auth_gateway/requirements.txt`
- `auth_gateway/security.py` · `hash_password` (l. 13), `verify_password` (l. 21), `valid_password` (l. 34)
- `auth_gateway/static/auth.css`
- `auth_gateway/static/auth.js`
- `auth_gateway/static/brand.css`
- `auth_gateway/static/darbly-mark.svg`
- `auth_gateway/static/mihna-mark.svg`
- `auth_gateway/templates/account.html`
- `auth_gateway/templates/base.html`
- `auth_gateway/templates/login.html`
- `auth_gateway/templates/register.html`
- `auth_gateway/tests/__init__.py`
- `auth_gateway/tests/test_gateway.py` · `FakeTunnel` (l. 15), `app_factory` (l. 30), `csrf_from` (l. 56), `register` (l. 62), `login` (l. 69), `test_register_valid_persists_hash_and_account_fields` (l. 74), `test_registration_validation` (l. 95), `test_duplicate_email_is_normalized_and_reported` (l. 103), `test_bad_password_is_generic_then_valid_login_and_logout_revokes_session` (l. 115), `test_private_routes_and_dash_are_protected_before_login` (l. 134), `test_login_csrf_and_safe_next_reject_external_redirect` (l. 139), `test_api_proxy_replaces_browser_csrf_with_private_backend_token` (l. 152), `test_legacy_backend_login_routes_cannot_bypass_gateway` (l. 167), `test_existing_application_logout_endpoint_invalidates_gateway_session` (l. 174), `test_rate_limit_applies_by_email_and_source_address` (l. 184), `test_expired_session_is_invalidated` (l. 193), `test_account_cookie_flags_and_persistence_across_app_restart` (l. 209), `test_private_profile_bootstraps_only_named_admin_and_disables_signup` (l. 225), `test_synthetic_demo_profile_does_not_allow_shared_account_registration` (l. 242), `test_gateway_refuses_nonisolated_private_mode_with_open_signup` (l. 250), `test_origin_and_csrf_block_cross_site_writes` (l. 260), `test_secure_cookie_flag_can_be_enabled` (l. 269), `test_configuration_fails_closed_for_public_backend_or_ephemeral_production_db` (l. 281), `MockResponse` (l. 300), `MockBackendHTTP` (l. 315), `test_backend_tunnel_uses_random_internal_channel_without_exposing_its_cookie` (l. 328), `test_backend_tunnel_rejects_demo_registration_on_private_backend` (l. 343), `test_gateway_local_port_check_does_not_take_over_existing_listener` (l. 353), `test_internal_secret_is_generated_and_reused_without_password_input` (l. 363), `test_demo_database_preflight_reads_synthetic_copy_only` (l. 376), `test_gateway_end_to_end_with_unchanged_flask_app_dash_chat_and_matching` (l. 391)
- `auth_gateway/verify_originals.py` · Compare les empreintes des fichiers préexistants sans parcourir les dossiers privés. · `main` (l. 13)
- `auth_gateway/wsgi.py` · Point WSGI de la passerelle. En production, le backend doit rester privé.
- `dashboard/alertes.html`
- `dashboard/analyses.html`
- `dashboard/assistant-carriere.html`
- `dashboard/candidatures.html`
- `dashboard/carte.html`
- `dashboard/collecte.html`
- `dashboard/competences.html`
- `dashboard/css/analytics.css`
- `dashboard/css/cv-preview.css`
- `dashboard/css/darbly-brand.css`
- `dashboard/css/darbly-mark.svg`
- `dashboard/css/design.css`
- `dashboard/css/map-leaflet.css`
- `dashboard/css/mihna-brand.css`
- `dashboard/css/mihna-mark.svg`
- `dashboard/css/mihna-system.css`
- `dashboard/css/mihna.css`
- `dashboard/css/phase5.css`
- `dashboard/css/studio.css`
- `dashboard/css/style.css`
- `dashboard/cv.html`
- `dashboard/entreprise.html`
- `dashboard/entreprises.html`
- `dashboard/entretiens.html`
- `dashboard/envoyer_cv.html`
- `dashboard/index.html`
- `dashboard/js/app.js`
- `dashboard/js/career-ai.js`
- `dashboard/js/cv-studio.js`
- `dashboard/js/gemini-status.js`
- `dashboard/js/mihna-pages.js`
- `dashboard/js/scrapers.js`
- `dashboard/js/ui.js`
- `dashboard/matching.html`
- `dashboard/offre.html`
- `dashboard/offres.html`
- `dashboard/parametres.html`
- `dashboard/parcours.html`
- `dashboard/profile.html`
- `dashboard/qualite-cv.html`
- `dashboard/recherche-ia.html`
- `dashboard/sauvegardes.html`
- `dashboard/statistiques.html`
- `database/gleif_ma.json`
- `scripts/analyse_exploratoire.py` · `main` (l. 8)
- `scripts/audit_donnees.py` · `main` (l. 9)
- `scripts/check_sources.py` · Lecture seule : robots.txt de Jawb.ma et Wadifa.info pour les adresses de flux prévues. · `main` (l. 14)
- `scripts/classifier_entreprises.py` · `main` (l. 9)
- `scripts/collect_entreprises.py` · `main` (l. 12)
- `scripts/collect_entreprises_complete.py` · `main` (l. 13)
- `scripts/collect_offres_marrakech.py` · `main` (l. 10)
- `scripts/collect_offres_stagiaires.py` · `main` (l. 8)
- `scripts/common.py` · Chemins et autorisation explicite des commandes de collecte. · `prepare` (l. 10)
- `scripts/create_candidatures_table.py` · `main` (l. 8)
- `scripts/create_database.py` · Import non destructif ; point d?entr?e historique conserv?.
- `scripts/create_public_demo_database.py` · Create a new, synthetic SQLite dataset for a read-only public demo. · `create_public_demo_database` (l. 13)
- `scripts/extract_emails.py` · `main` (l. 10)
- `scripts/generer_graphiques.py` · `main` (l. 10)
- `scripts/import_coordinates.py` · Import MANUEL de coordonnées vérifiées, sans aucun appel réseau. · `import_coordinates` (l. 14)
- `scripts/import_data.py` · Import Excel idempotent et non destructif. Sauvegarde avant chaque import. · `import_excel` (l. 10)
- `scripts/nettoyage_donnees.py` · `main` (l. 9)
- `scripts/phase11_3_import_wadifa.py` · Import staged Wadifa competitions only after matching the live feed and official URLs. · `verified_records` (l. 15), `import_records` (l. 47), `main` (l. 103)
- `scripts/phase12_browser.py` · Exercise the real gateway and browser against a disposable database. · `Quiet` (l. 28), `encode_video` (l. 33), `listen` (l. 41), `exercise` (l. 47), `main` (l. 242)
- `scripts/phase5_extract_free_apis.py` · Bounded Phase 5 extraction into an isolated JSONL staging file. · `main` (l. 20)
- `scripts/phase6_expand_extraction.py` · One-time Phase 6 filtered extraction to a new isolated JSONL file. · `_norm` (l. 32), `possible_duplicate_pairs` (l. 38), `stage_records` (l. 52), `main` (l. 80)
- `scripts/phase7_collect_gleif.py` · Take a tiny GLEIF Morocco identity sample into isolated JSONL staging. · `main` (l. 14)
- `scripts/phase7_collect_wadifa.py` · One bounded Wadifa Info public recruitment snapshot to isolated JSONL. · `main` (l. 15)
- `scripts/phase7_import_himalayas.py` · Preview or explicitly apply the validated Phase 7 Himalayas import. · `main` (l. 17)
- `scripts/phase7_validate_status.py` · Recheck unchecked Phase 6 Himalayas records; writes a separate JSONL file. · `main` (l. 19), `_parse_source_date` (l. 89)
- `scripts/places_client.py` · Places API (New) : client partagé, appelé uniquement par une commande autorisée. · `search_places` (l. 9)
- `scripts/run_scheduled_collection.py` · Lance un cycle planifié seulement si sources, droits et automatisation sont activés. · `main` (l. 7)
- `scripts/run_scrapers.py` · Collecte planifiable Jawb.ma / Wadifa.info vers le staging (jamais d'import automatique). · `main` (l. 21)
- `scripts/serve_public_demo.py` · Run a local, read-only demo using only the bundled synthetic database.
- `scripts/test_gemini.py` · Test RÉEL de Google Gemini avec la clé de votre fichier .env (à lancer sur votre ordinateur). · `main` (l. 18)
- `scripts/test_places_api.py` · `main` (l. 9)
- `scripts/verify_installation.py` · Read-only checks for a local Windows installation. · `verify_installation` (l. 30), `main` (l. 96)
- `scripts/verify_soutenance.py` · Vérifications en lecture seule du lancement local privé de soutenance. · `port_is_available` (l. 16), `inspect_environment` (l. 30), `main` (l. 90)
- `tests/browser_smoke.py` · Parcours réels Chrome/Playwright, sur copie anonymisée, sans réseau externe. · `QuietHandler` (l. 16), `main` (l. 21)
- `tests/conftest.py` · `no_external_network` (l. 12), `legacy_database` (l. 20), `app` (l. 41), `client` (l. 50), `cv_data` (l. 60), `cv_id` (l. 68), `reset_gemini_limits` (l. 75), `sdk_presence_for_simulated_clients` (l. 84)
- `tests/e2e_v2_navigateur.py` · Parcours navigateur réel (Chrome) : CV Studio, photo, couleurs, IA locale, assistant carrière, matching, responsive. · `check` (l. 15)
- `tests/test_analytics_dashboard.py` · `_walk` (l. 9), `test_dashboard_removes_collection_panel_and_preserves_analysis_filters` (l. 20), `test_dashboard_labels_synthetic_database_from_its_marker` (l. 41)
- `tests/test_application.py` · `test_migration_preserves_five_and_is_idempotent` (l. 18), `test_auth_and_csrf_required` (l. 32), `test_internal_gateway_session_requires_random_secret_and_loopback` (l. 39), `test_chat_rejects_stale_csrf_then_continues_after_authenticated_refresh` (l. 52), `test_assistant_mode_reports_gemini_only_when_fully_configured` (l. 66), `test_consultation_and_start_without_keys` (l. 77), `test_offers_prioritize_active_and_label_expired_or_unknown` (l. 85), `test_pages_connected` (l. 94), `test_invalid_application_rejected` (l. 102), `test_application_partial_update_and_history` (l. 107), `test_pdf_valid_and_extractable` (l. 120), `test_cv_preview_endpoint_returns_readable_pdf` (l. 130), `test_long_pdf_does_not_overflow` (l. 137), `test_cv_rejects_reversed_structured_period` (l. 144), `test_invalid_pdf_rejected` (l. 151), `test_pdf_extraction_endpoint` (l. 155), `test_cv_encrypted_and_versions` (l. 160), `test_cv_offer_optimization_is_local_grounded_and_non_destructive` (l. 170), `test_cv_summary_suggestion_reorders_only_existing_sentences` (l. 183), `test_cv_deletion_requires_existing_unreferenced_version` (l. 193), `test_local_matching_explainable` (l. 199), `test_matching_ranks_representative_profiles` (l. 210), `test_matching_invalid_weights` (l. 220), `test_gemini_consent_and_missing_api` (l. 224), `test_gemini_quota_falls_back` (l. 232), `test_gemini_actual_sdk_contract_mocked` (l. 239), `test_gemini_extraction_mocked` (l. 254), `test_anonymized_payload_and_stale_consent` (l. 261), `test_external_apply_confirmation_and_prepare` (l. 269), `test_no_channel_prepare` (l. 281), `smtp_body` (l. 288), `test_smtp_disabled_and_no_confirmation` (l. 293), `test_smtp_mocked_correct_recipient_and_idempotency` (l. 300), `test_smtp_untrusted_email_and_uncertain_failure` (l. 314), `test_dash_real_routes_and_callbacks` (l. 325), `test_dash_sector_filter_uses_only_explicit_verified_relations` (l. 341), `test_dash_incoherent_graph_explained` (l. 353), `test_coordinates_verified_and_import` (l. 360), `test_xss_data_never_rendered_as_html` (l. 370), `test_cross_origin_and_sensitive_files_denied` (l. 379), `test_scripts_import_without_side_effects` (l. 385), `test_excel_import_preserves_history_and_nonnull_contacts` (l. 391), `test_pdf_deterministic_for_idempotency` (l. 405), `test_pdf_export_authenticated_single_use` (l. 409), `test_places_pagination_mocked` (l. 419), `test_external_scripts_require_authorization` (l. 430), `test_official_sdk_accepts_structured_schema` (l. 436)
- `tests/test_auth_gateway_contract.py` · Expose les tests isolés de la passerelle au `pytest -q` habituel du projet.
- `tests/test_config_paths.py` · `test_relative_database_and_private_paths_are_anchored_to_project_root` (l. 6), `test_absolute_override_paths_are_preserved` (l. 18), `test_soutenance_port_check_detects_another_listener` (l. 26), `test_soutenance_verifier_rejects_public_demo_mode` (l. 40)
- `tests/test_free_apis.py` · `job` (l. 7), `Response` (l. 25), `Session` (l. 39), `HimalayasConnectorTests` (l. 49)
- `tests/test_gemini_integration.py` · Intégration Gemini : configuration, SDK, erreurs, mode local, non-exposition de la clé. · `FakeAPIError` (l. 23), `client_returning` (l. 29), `test_configuration_is_read_from_environment_and_tolerates_formatting` (l. 35), `test_env_file_with_bom_is_loaded` (l. 47), `test_incomplete_configuration_never_activates_gemini` (l. 62), `test_missing_sdk_is_detected_without_simulation` (l. 71), `test_sdk_client_initialised_with_key_and_timeout` (l. 79), `test_provider_errors_are_classified` (l. 106), `test_empty_response_is_invalid` (l. 113), `test_status_never_claims_connected_before_a_successful_real_check` (l. 120), `test_verification_accepts_empty_text_but_not_errors` (l. 136), `test_list_models_filters_generate_content` (l. 143), `test_local_mode_works_and_gemini_failure_falls_back` (l. 152), `test_gemini_cv_analysis_explains_weaknesses_without_invented_facts` (l. 163), `test_key_never_exposed_in_api_logs_or_errors` (l. 179), `test_startup_log_reports_configuration_without_key` (l. 194), `test_verify_endpoint_requires_session_and_is_blocked_in_public_demo` (l. 202), `test_env_is_ignored_by_git_and_example_has_no_real_key` (l. 207)
- `tests/test_gemini_real.py` · Appel RÉEL à Google Gemini — exécuté uniquement à la demande : · `allow_real_network` (l. 16), `test_real_gemini_connection` (l. 24)
- `tests/test_installation.py` · `make_project` (l. 15), `test_installation_checker_reads_required_files_and_sqlite` (l. 39), `test_installation_checker_explains_missing_env_and_venv` (l. 52), `test_installer_and_launcher_preserve_env_and_require_confirmation` (l. 64), `test_soutenance_launcher_pins_private_database_and_fails_closed` (l. 81), `test_legacy_launcher_forwards_to_new_launcher` (l. 96)
- `tests/test_map_dash.py` · `test_leaflet_is_served_locally_and_osm_is_allowed_by_csp` (l. 12), `test_map_keeps_historical_links_and_reports_only_verified_coordinates` (l. 29), `test_map_filter_displays_only_verified_company_markers` (l. 40), `test_dash_prefixes_and_return_link_leave_the_iframe` (l. 51), `test_verified_map_data_uses_only_imported_coordinate_provenance` (l. 70)
- `tests/test_mission10.py` · Tests de la mission 10 : service Gemini, CV Studio (couleurs, photo, modèles), assistants IA, · `image_bytes` (l. 25), `data_url` (l. 31), `fake_client` (l. 35), `gemini_app` (l. 45), `test_gemini_service_disabled_reasons_and_no_key_leak` (l. 51), `test_gemini_rate_limit_daily_quota_and_counter_file` (l. 61), `test_gemini_cache_avoids_repeated_calls` (l. 78), `test_gemini_errors_are_translated` (l. 91), `test_gemini_invalid_json_and_logs_without_content` (l. 96), `test_sdk_missing_is_reported_as_disabled` (l. 105), `test_palettes_custom_colors_and_contrast` (l. 113), `test_color_change_keeps_all_cv_information` (l. 126), `test_photo_is_optional_validated_and_reencoded` (l. 133), `test_photo_rejections` (l. 153), `test_photo_upload_endpoint_and_limits` (l. 158), `test_cv_with_photo_is_saved_encrypted_and_photo_can_be_removed` (l. 168), `test_every_template_renders_a4_pdf_with_and_without_photo` (l. 184), `test_long_cv_paginates_without_error` (l. 196), `test_preview_and_design_endpoints` (l. 202), `test_cv_assistant_local_actions_propose_without_modifying` (l. 213), `test_cv_assistant_never_invents_numbers_or_unproven_skills` (l. 231), `test_cv_assistant_gemini_requires_preview_consent_and_falls_back` (l. 248), `test_career_tasks_local` (l. 269), `test_career_gemini_letter_with_contact_details_is_rejected` (l. 283), `test_career_gemini_skills_must_be_quoted_from_offers` (l. 293), `test_matching_is_explainable_with_strengths_and_suggestions` (l. 303), `test_corpus_idf_matches_reference_formula` (l. 311), `test_city_is_inferred_from_offer_text_and_flagged` (l. 325), `test_vocabulary_avoids_french_false_positives` (l. 333), `test_quality_dates_deadlines_cities_and_urls` (l. 345), `FakeResponse` (l. 360), `FakeSession` (l. 366), `fetcher_for` (l. 389), `test_fetcher_respects_robots_protections_and_redirects` (l. 393), `test_jawb_collect_quality_without_descriptions` (l. 410), `test_wadifa_requires_explicit_feed_url` (l. 421), `test_scraper_pipeline_locked_then_staged_then_reviewed_import` (l. 429), `test_scraper_network_failure_is_logged_not_raised` (l. 462), `test_phase10_index_migration_backs_up_and_keeps_data` (l. 475), `test_offers_pagination_header` (l. 486), `test_app_starts_without_dash` (l. 493), `test_new_pages_are_served_and_csp_kept` (l. 505), `test_public_demo_allows_local_ai_only` (l. 513), `test_pdf_export_token_is_bound_to_its_session` (l. 528), `test_deleting_missing_alert_returns_404` (l. 538)
- `tests/test_phase10_frontend_contract.py` · Static guards for the dashboard modules (no browser needed). · `_kit_names` (l. 12), `test_modules_only_use_helpers_they_receive_from_ui_kit` (l. 18), `test_hidden_attribute_wins_over_button_display_rules` (l. 34), `test_tailoring_source_selector_lists_only_original_cvs` (l. 40), `test_dashboard_modules_parse_as_es_modules` (l. 45)
- `tests/test_phase10_tailored_cv.py` · Phase 10 factual tailoring, persistence, and application selection tests. · `test_tailoring_preview_preserves_source_and_never_inserts_missing_skills` (l. 6), `test_tailored_draft_validation_pdf_application_and_multiple_versions` (l. 20), `test_existing_account_workspace_gets_additive_tailoring_migration` (l. 53), `_validated_tailored` (l. 73), `test_identical_double_submission_does_not_create_a_duplicate` (l. 83), `test_tailored_version_cannot_be_used_as_source_and_original_stays_unchanged` (l. 94), `test_tailored_version_reopen_and_delete` (l. 105)
- `tests/test_phase115.py` · Phase 11.5 regressions for multilingual identity and verified source synchronization. · `test_arabic_fingerprints_and_job_query_identifiers` (l. 12), `test_jobicy_sync_preserves_history_and_uses_only_verified_open_jobs` (l. 18), `test_gleif_snapshot_search_keeps_legal_identity_separate` (l. 37), `test_location_and_contract_use_structured_evidence` (l. 45), `test_jobicy_access_and_quota_errors_stop_discovery` (l. 54)
- `tests/test_phase11_features.py` · Phase 11: saved offers, skills gap, CV quality, roadmap, analytics, company insights, · `saved_cv` (l. 24), `test_saved_offers_add_list_duplicate_remove` (l. 31), `test_skills_gap_separates_present_missing_and_never_claims_missing` (l. 45), `test_skills_gap_related_skills_and_requirements` (l. 55), `test_cv_quality_is_transparent_and_excludes_job_criterion_without_offer` (l. 66), `test_roadmap_uses_saved_offers_and_only_learning_steps_can_be_declared` (l. 80), `test_application_analytics_are_computed_from_records` (l. 97), `test_company_insights_show_only_stored_facts` (l. 115), `test_interview_history_reopen_assessment_and_delete` (l. 127), `test_dashboard_summary_and_personal_export` (l. 146), `test_gemini_feature_unavailable_is_explicit` (l. 158), `gemini_app` (l. 166), `_client` (l. 174), `_fake` (l. 182), `test_gemini_feature_requires_consent_and_filters_invented_claims` (l. 190), `test_gemini_tailored_summary_accepts_only_source_passage_ids` (l. 208), `test_gemini_quota_error_falls_back_to_local` (l. 222), `test_phase11_records_are_isolated_between_accounts` (l. 237), `test_migration_v11_is_additive_and_backed_up` (l. 261)
- `tests/test_phase12.py` · Phase 12 regressions for profile storage, CV edits, application status and resumable interviews. · `test_profile_country_and_original_cv_edit` (l. 5), `test_unsent_statuses_do_not_inflate_application_conversion` (l. 19), `test_interview_can_resume_and_finalize_without_duplicate_history` (l. 29), `test_optional_skills_do_not_reduce_coverage_and_remote_has_no_city_match` (l. 45)
- `tests/test_phase5.py` · `_offer` (l. 15), `_stage` (l. 19), `test_jawb_rss_parser_normalizes_and_keeps_source_link` (l. 28), `test_jawb_company_json_paginates_only_same_host` (l. 36), `test_empty_or_invalid_rss_and_bad_dates_are_not_fabricated` (l. 44), `test_collection_offers_incrementally_upserts_and_preserves_history` (l. 50), `test_cross_source_similar_offer_is_flagged_not_merged` (l. 63), `test_external_import_requires_rights_and_empty_run_never_deletes` (l. 74), `test_alert_filters_city_skills_expiry_and_deduplicates` (l. 86), `test_alert_preferences_are_bounded_and_explainable` (l. 103), `test_alert_email_requires_explicit_consent_and_uses_mock_smtp` (l. 109), `test_assistant_retrieves_only_database_rows_and_sanitizes_gemini` (l. 139), `test_assistant_counts_companies_and_uses_local_cv_matching_explanations` (l. 149), `test_assistant_gemini_can_only_reference_retrieved_ids` (l. 163), `test_company_csv_preview_and_import_are_non_destructive` (l. 171), `test_company_csv_rejects_unverified_coordinates_and_bad_urls` (l. 183), `test_dash_hides_collection_activity_but_keeps_collection_pages` (l. 188), `test_pipeline_end_to_end_synthetic_source_syncs_offers_matching_alerts_chatbot_and_dash` (l. 197), `test_external_preview_is_blocked_without_documented_source_rights` (l. 234), `test_unreviewed_staging_cannot_be_imported` (l. 244), `test_http_failure_is_logged_and_keeps_previously_imported_offers` (l. 254), `test_company_xlsx_preview_normalizes_sector_and_email` (l. 268)
- `tests/test_phase6_extraction.py` · `record` (l. 11), `Phase6StagingTests` (l. 23)
- `tests/test_phase7.py` · `_csv` (l. 13), `_file_form` (l. 18), `test_provided_offer_file_requires_all_rights_and_valid_https_urls` (l. 29), `test_provided_file_import_is_previewed_reviewed_and_syncs_all_local_modules` (l. 41), `test_provided_offer_file_upsert_is_idempotent` (l. 84), `test_source_register_separates_open_data_and_unlicensed_job_feeds` (l. 99), `test_network_source_settings_require_three_permission_scopes_and_https` (l. 112), `test_phase7_import_preview_backup_attribution_and_company_separation` (l. 132), `test_phase7_import_rejects_unverified_and_duplicate_ids` (l. 179)
- `tests/test_phase7_import_unittest.py` · Dependency-light isolated tests for the Phase 7 import safety path. · `Phase7ImportTests` (l. 14)
- `tests/test_phase8.py` · `offer` (l. 20), `Response` (l. 26), `Session` (l. 40), `test_greenhouse_mocked_fetch_and_empty_payload` (l. 49), `test_lever_mocked_pagination_and_normalization` (l. 57), `test_ashby_omits_unlisted_jobs_and_keeps_listed_job_fields` (l. 68), `test_smartrecruiters_public_filter_and_pagination` (l. 79), `test_platform_errors_and_http_failures_are_clear` (l. 91), `test_csv_column_mapping_and_date_url_rejections` (l. 102), `test_xlsx_manual_import_mapping_and_company_mapping` (l. 112), `test_classification_is_explainable_and_unknown_is_not_a_stage` (l. 129), `test_board_registry_refuses_activation_without_all_rights` (l. 138), `test_authorized_rss_registry_is_gated_by_global_external_switch` (l. 150), `test_mock_connector_runs_through_staging_validation_and_local_modules` (l. 163)
- `tests/test_phase9.py` · `FakeModels` (l. 17), `FakeClient` (l. 25), `config` (l. 30), `response` (l. 36), `test_grounding_sources_citations_and_search_count` (l. 48), `test_no_grounding_means_no_importable_link_even_if_model_invents_one` (l. 58), `test_untrusted_or_internal_grounding_urls_are_filtered` (l. 68), `test_invalid_structured_response_and_provider_error_are_rejected` (l. 72), `test_search_requires_enabled_key_and_billing_configuration` (l. 80), `test_local_search_and_demo_workflow_leave_main_db_unchanged` (l. 87), `test_gemini_route_never_runs_when_not_configured` (l. 106), `test_gemini_quota_and_cancel_suppress_returned_results` (l. 115), `test_staging_requires_manual_verification_rights_and_source` (l. 142)
- `tests/test_phase9_profile_workflows.py` · Phase 9 account-profile and notification safety regression tests. · `test_profile_persists_and_prefills_only_selected_cv_sections` (l. 5), `test_interview_history_is_encrypted_and_only_saved_after_explicit_request` (l. 32), `test_cv_section_order_is_preserved_in_pdf` (l. 52), `test_alert_email_requires_explicit_consent_and_smtp` (l. 64)
- `tests/test_public_demo.py` · `test_public_demo_is_synthetic_read_only_and_private_data_free` (l. 10), `test_public_mode_refuses_database_without_synthetic_marker` (l. 47), `test_public_mode_requires_explicit_data_attestation` (l. 55)
- `tests/test_user_isolation.py` · `test_multi_user_backend_isolates_personal_data_and_preserves_historical_source` (l. 6), `test_per_user_dash_reads_the_matching_isolated_database` (l. 110)

## Routes déclarées dans le code

| Méthode | Chemin déclaré | Gestionnaire | Fichier |
|---|---|---|---|
| GET | `/api/ai/status` | `ai_status` | [backend/ai_routes.py](../backend/ai_routes.py#L71) |
| POST | `/api/ai/verify` | `ai_verify` | [backend/ai_routes.py](../backend/ai_routes.py#L78) |
| GET | `/api/cvs/design-options` | `design_options` | [backend/ai_routes.py](../backend/ai_routes.py#L89) |
| POST | `/api/cvs/design/check` | `design_check` | [backend/ai_routes.py](../backend/ai_routes.py#L97) |
| POST | `/api/cvs/photo` | `upload_photo` | [backend/ai_routes.py](../backend/ai_routes.py#L103) |
| POST | `/api/ai/cv/<action>/preview` | `cv_assist_preview` | [backend/ai_routes.py](../backend/ai_routes.py#L129) |
| POST | `/api/ai/cv/<action>` | `cv_assist` | [backend/ai_routes.py](../backend/ai_routes.py#L137) |
| POST | `/api/ai/career/<task>/preview` | `career_preview` | [backend/ai_routes.py](../backend/ai_routes.py#L181) |
| POST | `/api/ai/career/<task>` | `career` | [backend/ai_routes.py](../backend/ai_routes.py#L189) |
| POST | `/api/ai/interview/feedback/preview` | `interview_feedback_preview` | [backend/ai_routes.py](../backend/ai_routes.py#L223) |
| POST | `/api/ai/interview/feedback` | `interview_feedback_route` | [backend/ai_routes.py](../backend/ai_routes.py#L231) |
| GET | `/api/entreprises` | `get_companies` | [backend/api.py](../backend/api.py#L186) |
| GET | `/api/offres` | `get_offers` | [backend/api.py](../backend/api.py#L191) |
| GET | `/api/statistiques` | `statistics` | [backend/api.py](../backend/api.py#L211) |
| GET | `/api/profile` | `get_profile` | [backend/api.py](../backend/api.py#L247) |
| PUT | `/api/profile` | `put_profile` | [backend/api.py](../backend/api.py#L253) |
| GET | `/api/profile/cv-draft` | `profile_cv_draft` | [backend/api.py](../backend/api.py#L265) |
| GET | `/api/career/interviews` | `interview_history` | [backend/api.py](../backend/api.py#L272) |
| GET | `/api/career/interview-drafts` | `interview_drafts` | [backend/api.py](../backend/api.py#L304) |
| PUT | `/api/career/interview-drafts` | `save_interview_draft` | [backend/api.py](../backend/api.py#L314) |
| POST | `/api/career/interviews` | `save_interview_history` | [backend/api.py](../backend/api.py#L333) |
| GET | `/api/candidatures` | `get_applications` | [backend/api.py](../backend/api.py#L351) |
| POST | `/api/candidatures` | `create_application` | [backend/api.py](../backend/api.py#L356) |
| PUT, PATCH | `/api/candidatures/<int:ident>` | `update_application` | [backend/api.py](../backend/api.py#L364) |
| DELETE | `/api/candidatures/<int:ident>` | `delete_application` | [backend/api.py](../backend/api.py#L379) |
| GET | `/api/candidatures/<int:ident>/history` | `history` | [backend/api.py](../backend/api.py#L385) |
| GET | `/api/attempts` | `attempts` | [backend/api.py](../backend/api.py#L390) |
| GET | `/api/cvs` | `list_cvs` | [backend/api.py](../backend/api.py#L395) |
| POST | `/api/cvs` | `save_cv` | [backend/api.py](../backend/api.py#L400) |
| PATCH | `/api/cvs/<int:ident>` | `edit_cv` | [backend/api.py](../backend/api.py#L405) |
| GET | `/api/cvs/tailored` | `list_tailored_cvs` | [backend/api.py](../backend/api.py#L431) |
| POST | `/api/cvs/tailored/preview` | `preview_tailored_cv` | [backend/api.py](../backend/api.py#L437) |
| POST | `/api/cvs/tailored` | `create_tailored_cv` | [backend/api.py](../backend/api.py#L557) |
| PATCH | `/api/cvs/<int:ident>/tailored` | `update_tailored_cv` | [backend/api.py](../backend/api.py#L563) |
| GET | `/api/cvs/<int:ident>` | `read_cv` | [backend/api.py](../backend/api.py#L568) |
| DELETE | `/api/cvs/<int:ident>` | `delete_cv` | [backend/api.py](../backend/api.py#L573) |
| POST | `/api/cvs/optimize` | `optimize_cv` | [backend/api.py](../backend/api.py#L586) |
| GET | `/api/cvs/<int:ident>/pdf` | `cv_pdf` | [backend/api.py](../backend/api.py#L639) |
| POST | `/api/cvs/preview` | `preview_cv` | [backend/api.py](../backend/api.py#L648) |
| POST | `/api/cvs/export` | `prepare_pdf_export` | [backend/api.py](../backend/api.py#L654) |
| GET | `/api/cvs/export/<token>` | `download_pdf_export` | [backend/api.py](../backend/api.py#L670) |
| POST | `/api/profile/extract` | `extract_profile` | [backend/api.py](../backend/api.py#L678) |
| POST | `/api/profile/gemini/preview` | `profile_gemini_preview` | [backend/api.py](../backend/api.py#L687) |
| POST | `/api/profile/gemini` | `profile_gemini` | [backend/api.py](../backend/api.py#L695) |
| POST | `/api/matching/preview` | `matching_preview` | [backend/api.py](../backend/api.py#L719) |
| POST | `/api/matching` | `matching` | [backend/api.py](../backend/api.py#L725) |
| GET | `/api/offres/<int:ident>/application` | `application_context` | [backend/api.py](../backend/api.py#L750) |
| POST | `/api/offres/<int:ident>/apply` | `apply` | [backend/api.py](../backend/api.py#L763) |
| POST | `/api/envoyer-cv` | `send_company_cv` | [backend/api.py](../backend/api.py#L808) |
| GET | `/api/map` | `map_data` | [backend/api.py](../backend/api.py#L831) |
| GET | `/api/collect/summary` | `collect_summary` | [backend/api.py](../backend/api.py#L842) |
| POST | `/api/collect/offers/file/preview` | `collect_provided_offers_preview` | [backend/api.py](../backend/api.py#L847) |
| GET, POST | `/api/collect/settings` | `collect_settings` | [backend/api.py](../backend/api.py#L862) |
| GET, POST | `/api/collect/runs` | `collect_runs` | [backend/api.py](../backend/api.py#L885) |
| GET | `/api/collect/runs/<int:ident>` | `collect_run_detail` | [backend/api.py](../backend/api.py#L895) |
| POST | `/api/collect/runs/<int:ident>/staged/<int:stage_id>/decision` | `collect_stage_decision` | [backend/api.py](../backend/api.py#L902) |
| POST | `/api/collect/runs/<int:ident>/import` | `collect_run_import` | [backend/api.py](../backend/api.py#L908) |
| GET | `/api/ai-search/status` | `ai_search_status` | [backend/api.py](../backend/api.py#L932) |
| POST | `/api/ai-search/local` | `ai_search_local` | [backend/api.py](../backend/api.py#L950) |
| POST | `/api/ai-search/demo` | `ai_search_demo` | [backend/api.py](../backend/api.py#L957) |
| POST | `/api/ai-search/gemini` | `ai_search_gemini` | [backend/api.py](../backend/api.py#L970) |
| GET | `/api/ai-search/jobs/<ident>` | `ai_search_job` | [backend/api.py](../backend/api.py#L996) |
| POST | `/api/ai-search/jobs/<ident>/cancel` | `ai_search_cancel` | [backend/api.py](../backend/api.py#L1003) |
| POST | `/api/ai-search/jobs/<ident>/stage` | `ai_search_stage` | [backend/api.py](../backend/api.py#L1012) |
| GET | `/api/ai-search/history` | `ai_search_history` | [backend/api.py](../backend/api.py#L1035) |
| DELETE | `/api/ai-search/history` | `ai_search_clear_history` | [backend/api.py](../backend/api.py#L1040) |
| POST | `/api/collect/companies/import` | `collect_companies_import` | [backend/api.py](../backend/api.py#L1047) |
| GET | `/api/alerts/preferences` | `get_alert_preferences` | [backend/api.py](../backend/api.py#L1065) |
| PUT | `/api/alerts/preferences` | `put_alert_preferences` | [backend/api.py](../backend/api.py#L1074) |
| GET | `/api/alerts` | `get_alerts` | [backend/api.py](../backend/api.py#L1105) |
| GET | `/api/alerts/count` | `alert_count` | [backend/api.py](../backend/api.py#L1114) |
| POST | `/api/alerts/<int:ident>/read` | `mark_alert_read` | [backend/api.py](../backend/api.py#L1119) |
| POST | `/api/alerts/read-all` | `mark_alerts_read` | [backend/api.py](../backend/api.py#L1127) |
| DELETE | `/api/alerts/<int:ident>` | `delete_alert` | [backend/api.py](../backend/api.py#L1133) |
| GET | `/api/assistant/history` | `assistant_history` | [backend/api.py](../backend/api.py#L1162) |
| GET | `/api/assistant/status` | `assistant_status` | [backend/api.py](../backend/api.py#L1172) |
| DELETE | `/api/assistant/history` | `clear_assistant_history` | [backend/api.py](../backend/api.py#L1181) |
| POST | `/api/assistant/preview` | `assistant_preview` | [backend/api.py](../backend/api.py#L1195) |
| POST | `/api/assistant/chat` | `assistant_chat` | [backend/api.py](../backend/api.py#L1202) |
| GET | `/api/saved-offers` | `list_saved` | [backend/phase11_routes.py](../backend/phase11_routes.py#L53) |
| POST | `/api/saved-offers` | `save_offer` | [backend/phase11_routes.py](../backend/phase11_routes.py#L65) |
| DELETE | `/api/saved-offers/<int:offer_id>` | `unsave_offer` | [backend/phase11_routes.py](../backend/phase11_routes.py#L80) |
| GET | `/api/saved-offers/ids` | `saved_ids` | [backend/phase11_routes.py](../backend/phase11_routes.py#L89) |
| POST | `/api/skills-gap` | `skills_gap_route` | [backend/phase11_routes.py](../backend/phase11_routes.py#L95) |
| POST | `/api/cv-quality` | `cv_quality_route` | [backend/phase11_routes.py](../backend/phase11_routes.py#L110) |
| GET | `/api/roadmap` | `get_roadmap` | [backend/phase11_routes.py](../backend/phase11_routes.py#L184) |
| PUT | `/api/roadmap` | `put_roadmap` | [backend/phase11_routes.py](../backend/phase11_routes.py#L189) |
| GET | `/api/analytics/applications` | `applications_analytics` | [backend/phase11_routes.py](../backend/phase11_routes.py#L227) |
| GET | `/api/candidatures/export.csv` | `export_applications_csv` | [backend/phase11_routes.py](../backend/phase11_routes.py#L244) |
| GET | `/api/me/export` | `export_my_data` | [backend/phase11_routes.py](../backend/phase11_routes.py#L258) |
| GET | `/api/companies/lei` | `company_lei_route` | [backend/phase11_routes.py](../backend/phase11_routes.py#L284) |
| GET | `/api/companies/overview` | `companies_overview_route` | [backend/phase11_routes.py](../backend/phase11_routes.py#L291) |
| GET | `/api/companies/<int:ident>/insights` | `company_insights_route` | [backend/phase11_routes.py](../backend/phase11_routes.py#L296) |
| GET | `/api/career/interviews/<ident>` | `interview_detail` | [backend/phase11_routes.py](../backend/phase11_routes.py#L322) |
| GET | `/api/career/interviews-summary` | `interview_summary` | [backend/phase11_routes.py](../backend/phase11_routes.py#L330) |
| DELETE | `/api/career/interviews/<ident>` | `interview_delete` | [backend/phase11_routes.py](../backend/phase11_routes.py#L337) |
| GET | `/api/dashboard` | `dashboard` | [backend/phase11_routes.py](../backend/phase11_routes.py#L346) |
| POST | `/api/ai/feature/<feature>/preview` | `feature_preview` | [backend/phase11_routes.py](../backend/phase11_routes.py#L500) |
| POST | `/api/ai/feature/<feature>` | `feature_run` | [backend/phase11_routes.py](../backend/phase11_routes.py#L511) |
| GET | `/api/ai/features` | `feature_list` | [backend/phase11_routes.py](../backend/phase11_routes.py#L543) |
| GET | `/api/scrapers` | `scraper_status` | [backend/scraper_routes.py](../backend/scraper_routes.py#L12) |
| POST | `/api/scrapers/<source>/config` | `scraper_config` | [backend/scraper_routes.py](../backend/scraper_routes.py#L18) |
| POST | `/api/scrapers/<source>/run` | `scraper_run` | [backend/scraper_routes.py](../backend/scraper_routes.py#L24) |
| GET | `/api/auth/session` | `auth_session` | [backend/web.py](../backend/web.py#L142) |
| POST | `/api/auth/setup` | `setup` | [backend/web.py](../backend/web.py#L152) |
| POST | `/api/auth/login` | `login` | [backend/web.py](../backend/web.py#L169) |
| POST | `/api/auth/logout` | `logout` | [backend/web.py](../backend/web.py#L184) |
| POST | `/api/internal/gateway-session` | `internal_gateway_session` | [backend/web.py](../backend/web.py#L189) |
| GET | `/favicon.ico` | `favicon` | [backend/web.py](../backend/web.py#L201) |
| GET | `/health` | `health` | [backend/web.py](../backend/web.py#L205) |
| GET | `/test-db` | `test_db` | [backend/web.py](../backend/web.py#L209) |
| GET | `/` | `home` | [backend/web.py](../backend/web.py#L214) |
| GET | `/<path:filename>` | `frontend` | [backend/web.py](../backend/web.py#L218) |
| GET | `/analytics/` | `analytics_unavailable` | [backend/web.py](../backend/web.py#L260) |
| GET | `/health` | `gateway_health` | [auth_gateway/app.py](../auth_gateway/app.py#L196) |
| GET, POST | `/login` | `gateway_login` | [auth_gateway/app.py](../auth_gateway/app.py#L200) |
| GET, POST | `/register` | `gateway_register` | [auth_gateway/app.py](../auth_gateway/app.py#L228) |
| GET | `/account` | `gateway_account` | [auth_gateway/app.py](../auth_gateway/app.py#L267) |
| POST | `/auth/logout` | `gateway_logout` | [auth_gateway/app.py](../auth_gateway/app.py#L272) |
| GET | `/api/auth/session` | `gateway_auth_session` | [auth_gateway/app.py](../auth_gateway/app.py#L282) |
| POST | `/api/auth/logout` | `gateway_api_logout` | [auth_gateway/app.py](../auth_gateway/app.py#L290) |
| GET, POST | `/api/auth/login` | `block_legacy_auth` | [auth_gateway/app.py](../auth_gateway/app.py#L303) |
| GET, POST | `/api/auth/setup` | `block_legacy_auth` | [auth_gateway/app.py](../auth_gateway/app.py#L303) |
| GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS | `/` | `proxy_to_application` | [auth_gateway/app.py](../auth_gateway/app.py#L308) |
| GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS | `/<path:path>` | `proxy_to_application` | [auth_gateway/app.py](../auth_gateway/app.py#L308) |
