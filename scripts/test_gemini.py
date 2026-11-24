"""Test RÉEL de Google Gemini avec la clé de votre fichier .env (à lancer sur votre ordinateur).

    .venv\\Scripts\\python.exe scripts\\test_gemini.py            -> une requête courte réelle
    .venv\\Scripts\\python.exe scripts\\test_gemini.py --models   -> + modèles disponibles pour VOTRE clé

Affiche uniquement : connexion réussie/échouée, modèle, temps de réponse, type d'erreur.
La clé API n'est jamais affichée ; aucun message brut du fournisseur n'est imprimé.
Codes de sortie : 0 succès, 1 échec de connexion, 2 configuration incomplète.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Test réel de Gemini')
    parser.add_argument('--models', action='store_true', help='lister les modèles Gemini disponibles pour cette clé')
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')  # console Windows : jamais de plantage d'affichage
    from backend.config import settings
    from backend.services.gemini_service import ERROR_LABELS, GeminiError, GeminiService

    cfg = settings()
    service = GeminiService(cfg)
    state = service.status()
    print('Fichier .env trouvé      :', 'oui' if (ROOT / '.env').exists() else 'NON')
    print('GEMINI_ENABLED           :', cfg['GEMINI_ENABLED'])
    print('GEMINI_API_KEY présente  :', 'oui' if state['key_present'] else 'NON')   # la valeur n'est jamais affichée
    print('GEMINI_FREE_TIER_CONFIRMED:', cfg['GEMINI_FREE_TIER_CONFIRMED'])
    print('SDK google-genai installé:', 'oui' if state['sdk_installed'] else 'NON')
    print('Modèle utilisé           :', service.model)
    if not state['enabled']:
        print('\nRÉSULTAT : connexion NON testée — configuration incomplète :')
        for reason in state['reasons']:
            print('  -', reason)
        return 2

    if args.models:
        try:
            names = service.list_models()
            print('\nModèles Gemini disponibles pour cette clé :', ', '.join(names) or '(aucun)')
            if service.model not in names:
                print('ATTENTION : le modèle configuré n’apparaît pas dans cette liste. Choisissez-en un dans GEMINI_MODEL.')
        except GeminiError as exc:
            print('\nListe des modèles indisponible :', ERROR_LABELS.get(exc.code, exc.code))

    result = service.verify_connection()
    print()
    if result['ok']:
        print('RÉSULTAT          : CONNEXION RÉUSSIE (vraie requête Google Gemini)')
        print('Modèle            :', result['model'])
        print('Temps de réponse  :', result['latency_ms'], 'ms')
        print('Texte reçu        :', 'oui' if result.get('reply_received') else 'non (réponse vide mais appel accepté)')
        return 0
    print('RÉSULTAT          : CONNEXION ÉCHOUÉE')
    print('Modèle            :', result['model'])
    print('Temps écoulé      :', result['latency_ms'], 'ms')
    print('Type d’erreur     :', result.get('error_code'), '—', result.get('error_label'))
    print('Que faire         :', result.get('message'))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
