import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _flag(name, default='false'):
    # Tolère « true », « True », « 1 », « oui », espaces ou guillemets parasites dans .env.
    return os.getenv(name, default).strip().strip('"').strip("'").strip().lower() in ('true', '1', 'yes', 'oui', 'on')


def _text(name, default=''):
    return os.getenv(name, default).strip().strip('"').strip("'").strip()


def settings(overrides=None):
    from dotenv import load_dotenv
    # utf-8-sig : un .env enregistré par le Bloc-notes avec BOM reste lisible.
    load_dotenv(ROOT / '.env', override=False, encoding='utf-8-sig')
    values = dict(
        ROOT=ROOT, DATABASE=os.getenv('DATABASE', str(ROOT / 'database/stages_marrakech.db')),
        PRIVATE_DIR=os.getenv('PRIVATE_DIR', str(ROOT / 'private')), BACKUP_DIR=os.getenv('BACKUP_DIR', str(ROOT / 'backups')),
        TRUSTED_HOSTS=[x.strip() for x in os.getenv('TRUSTED_HOSTS','127.0.0.1,localhost,[::1]').split(',') if x.strip()],
        PUBLIC_DEMO_MODE=os.getenv('PUBLIC_DEMO_MODE','false').lower()=='true',
        PUBLIC_DEMO_DATA_CONFIRMED=os.getenv('PUBLIC_DEMO_DATA_CONFIRMED','false').lower()=='true',
        TRUST_PROXY=os.getenv('TRUST_PROXY','false').lower()=='true',
        MAX_CONTENT_LENGTH=6 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict',
        SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE', 'false').lower() == 'true',
        SMTP_ENABLED=os.getenv('SMTP_ENABLED', 'false').lower() == 'true',
        SMTP_HOST=os.getenv('SMTP_HOST', 'smtp.gmail.com'), SMTP_PORT=int(os.getenv('SMTP_PORT', '587')),
        SMTP_USER=os.getenv('SMTP_USER', ''), SMTP_PASSWORD=os.getenv('SMTP_PASSWORD', ''),
        GEMINI_ENABLED=_flag('GEMINI_ENABLED'),
        GEMINI_API_KEY=_text('GEMINI_API_KEY'), GEMINI_MODEL=_text('GEMINI_MODEL', 'gemini-3.1-flash-lite') or 'gemini-3.1-flash-lite',
        GEMINI_FREE_TIER_CONFIRMED=_flag('GEMINI_FREE_TIER_CONFIRMED'),
        GEMINI_ALLOWED_MODELS=_text('GEMINI_ALLOWED_MODELS'),
        GEMINI_TIMEOUT_SECONDS=int(os.getenv('GEMINI_TIMEOUT_SECONDS', '20')),
        GEMINI_RATE_PER_MINUTE=int(os.getenv('GEMINI_RATE_PER_MINUTE', '8')),
        GEMINI_DAILY_LIMIT=int(os.getenv('GEMINI_DAILY_LIMIT', '200')),
        GEMINI_CACHE_TTL_SECONDS=int(os.getenv('GEMINI_CACHE_TTL_SECONDS', '900')),
        GEMINI_SEARCH_ENABLED=_flag('GEMINI_SEARCH_ENABLED'),
        GEMINI_SEARCH_MODEL=os.getenv('GEMINI_SEARCH_MODEL', 'gemini-3.8-flash'),
        GEMINI_SEARCH_BILLING_CONFIRMED=_flag('GEMINI_SEARCH_BILLING_CONFIRMED'),
        GEMINI_SEARCH_MAX_SESSION=int(os.getenv('GEMINI_SEARCH_MAX_SESSION', '2')),
        GEMINI_SEARCH_MAX_DAILY=int(os.getenv('GEMINI_SEARCH_MAX_DAILY', '5')),
        GEMINI_SEARCH_COOLDOWN_SECONDS=int(os.getenv('GEMINI_SEARCH_COOLDOWN_SECONDS', '60')),
        GEMINI_SEARCH_TIMEOUT_MS=int(os.getenv('GEMINI_SEARCH_TIMEOUT_MS', '30000')),
        MAPS_ENABLED=os.getenv('MAPS_ENABLED', 'false').lower() == 'true', MAPS_BROWSER_KEY=os.getenv('MAPS_BROWSER_KEY', ''),
        MATCH_WEIGHTS={'skills': 40, 'education': 25, 'experience': 15, 'location': 10, 'opportunity': 10},
        TESTING=False,
    )
    if overrides:
        values.update(overrides)
    for key in ('DATABASE', 'PRIVATE_DIR', 'BACKUP_DIR'):
        path = Path(values[key]).expanduser()
        values[key] = str(path.resolve() if path.is_absolute() else (ROOT / path).resolve())
    return values
