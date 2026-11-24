# Mihna — Audit final

## Phase 13

- Le catalogue a reçu huit nouveaux concours dans une transaction couvrant la base principale et l’espace existant. Le nouvel import a été joué deux fois sur des copies avant insertion.
- Les règles d’exclusion Git couvrent désormais les fichiers d’environnement locaux, les secrets, les données de la passerelle, les sauvegardes et les artefacts de travail.
- La base de préparation au déploiement a été créée séparément avec huit offres publiques et zéro dossier personnel. Les identités légales publiques restent dans le référentiel GLEIF fourni avec le code.
- La remise reste conditionnée par une copie lisible de la présentation de référence, une session GitHub autorisée et un hébergement persistant vérifié.

## Phase 12

Mihna still uses the Flask application, the local authentication gateway, the v11 SQLite catalog and separate user workspaces. Phase 12 uses existing encrypted profile, CV and interview storage. There is no migration and no production fixture injection.

| Issue | Cause and change | Verification |
|---|---|---|
| No country field | Added an optional field to the encrypted profile and form | Save, reload and older profile handling |
| Editing a saved original created another CV | Added a dedicated original-CV update route and tracked the selected original in the editor | Two originals remain independently editable; tailored versions use their separate route |
| Application tracker could not express preparation and review states | Added Draft, Ready, External unconfirmed, Under review and Withdrawn while preserving legacy labels | New states remain out of confirmed submission metrics where appropriate |
| Answers were lost before feedback | Added encrypted per-account interview drafts with resume and atomic finalization | Reopen with the same CV and offer; draft is omitted from completed history |
| Old matching results could reappear after changes | Revision-guarded responses, cleared results and protected CV loading | Local matching with saved CV and recalculation |
| Concurrent first profile reads could race | Insert-if-absent and read the stored result | Initial synthetic account profile tests |

| Optional skills could count against the CV, and remote text could trigger a local-city score | Separate explicit optional clauses and skip city scoring for structured remote listings | Optional-skill and remote location regressions |
| Drafts and withdrawals could distort conversion | Use distinct application IDs with confirmed submission history and deduplicate response events | Conversion regression with a withdrawn interview |
| Alert tests could race the background scheduler, and concurrent senders could claim the same queue | Scheduler activation now respects app mode. SQLite claims alert email rows before a worker sends them | Mocked SMTP and full-suite reruns |

See [feature verification](FINAL_FEATURE_VERIFICATION_MATRIX.md), [test results](FINAL_TEST_RESULTS.md) and [known limitations](FINAL_KNOWN_LIMITATIONS.md) for evidence and remaining coverage.
