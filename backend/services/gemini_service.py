"""Service Gemini centralisé.

Toutes les fonctionnalités IA du projet passent par ce module :
- SDK officiel ``google-genai`` (import paresseux : l'application démarre sans lui) ;
- clé lue uniquement dans la configuration (variable d'environnement ``GEMINI_API_KEY``) ;
- liste de modèles autorisés, délai d'expiration, limitation par minute, quota quotidien ;
- cache mémoire court pour éviter les appels répétitifs identiques ;
- erreurs traduites en messages compréhensibles ;
- journalisation sans contenu : tâche, modèle, statut, durée — jamais le texte envoyé ni la clé.

Le mode local de secours est décidé par l'appelant : toute ``GeminiError`` signifie
« utiliser la version locale ».
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict, deque
from datetime import date
from pathlib import Path

logger = logging.getLogger('stages.gemini')

# Modèles stables vérifiés dans la documentation officielle (ai.google.dev, novembre 2026).
DEFAULT_MODEL = 'gemini-3.5-flash-lite'
DEFAULT_ALLOWED_MODELS = ('gemini-3.5-flash-lite', 'gemini-3.1-flash-lite', 'gemini-3.6-flash', 'gemini-3.8-flash')


class GeminiError(ValueError):
    """Erreur générique : l'appelant doit basculer en mode local (sous-classe de ValueError → HTTP 400 lisible)."""
    code = 'unavailable'
    user_message = 'Gemini est momentanément indisponible. La version locale est utilisée.'

    def __init__(self, message=None):
        super().__init__(message or self.user_message)
        if message:
            self.user_message = message


class GeminiDisabled(GeminiError):
    code = 'disabled'
    user_message = 'Gemini n’est pas activé sur cette installation. La version locale est utilisée.'


class GeminiRateLimited(GeminiError):
    code = 'rate_limited'
    user_message = 'Trop de demandes IA en peu de temps. Patientez une minute ; la version locale est utilisée.'


class GeminiQuotaExceeded(GeminiError):
    code = 'quota'
    user_message = 'Quota Gemini atteint (local ou fournisseur). La version locale est utilisée.'


class GeminiTimeout(GeminiError):
    code = 'timeout'
    user_message = 'Gemini n’a pas répondu à temps. La version locale est utilisée.'


class GeminiAuthError(GeminiError):
    code = 'auth'
    user_message = 'La clé Gemini est refusée par Google (clé invalide ou API non activée). Prévenez l’administrateur.'


class GeminiNetworkError(GeminiError):
    code = 'network'
    user_message = 'Impossible de joindre Google Gemini (pas de connexion Internet, DNS ou pare-feu). La version locale est utilisée.'


class GeminiModelUnavailable(GeminiError):
    code = 'model_unavailable'
    user_message = 'Le modèle Gemini configuré n’est pas disponible pour cette clé. Vérifiez GEMINI_MODEL (scripts\\test_gemini.py --models).'


class GeminiInvalidResponse(GeminiError):
    code = 'invalid_response'
    user_message = 'La réponse de Gemini n’a pas pu être vérifiée. La version locale est utilisée.'


ERROR_LABELS = {
    'disabled': 'Gemini désactivé ou incomplet dans .env', 'auth': 'Clé API refusée (invalide, révoquée ou API non activée)',
    'quota': 'Quota dépassé (429)', 'rate_limited': 'Limite locale par minute atteinte', 'timeout': 'Délai dépassé',
    'network': 'Pas de connexion Internet / Google injoignable', 'model_unavailable': 'Modèle indisponible pour cette clé',
    'invalid_response': 'Réponse vide ou invalide', 'unavailable': 'Service Gemini indisponible',
}
_VERIFICATION = {}   # empreinte (modèle + hachage de la clé) -> dernier résultat de test réel

_STATE_LOCK = threading.Lock()
_CALLS = deque()               # horodatages monotoniques des appels de la dernière minute
_CACHE: OrderedDict = OrderedDict()  # clé -> (expiration, valeur)
_CACHE_MAX = 64


def _flag(value):
    return value is True or str(value).strip().lower() in ('1', 'true', 'yes', 'oui')


def _int(config, key, default):
    try:
        return max(0, int(config.get(key, default)))
    except (TypeError, ValueError):
        return default


def allowed_models(config):
    raw = config.get('GEMINI_ALLOWED_MODELS')
    if isinstance(raw, str) and raw.strip():
        return tuple(m.strip() for m in raw.split(',') if m.strip())
    if isinstance(raw, (list, tuple)) and raw:
        return tuple(raw)
    return DEFAULT_ALLOWED_MODELS


class GeminiService:
    def __init__(self, config, client_factory=None):
        self.config = config or {}
        self.client_factory = client_factory

    # ------------------------------------------------------------------ état
    @property
    def model(self):
        return str(self.config.get('GEMINI_MODEL') or DEFAULT_MODEL).strip()

    @property
    def timeout_ms(self):
        return _int(self.config, 'GEMINI_TIMEOUT_SECONDS', 20) * 1000 or 20000

    @property
    def rate_per_minute(self):
        return _int(self.config, 'GEMINI_RATE_PER_MINUTE', 8)

    @property
    def daily_limit(self):
        return _int(self.config, 'GEMINI_DAILY_LIMIT', 200)

    @property
    def cache_ttl(self):
        return _int(self.config, 'GEMINI_CACHE_TTL_SECONDS', 900)

    @property
    def api_key(self):
        # Espaces, retours chariot et guillemets parasites issus d'un copier-coller dans .env.
        return str(self.config.get('GEMINI_API_KEY') or '').strip().strip('"').strip("'").strip()

    def _fingerprint(self):
        # Identifie la configuration testée sans jamais conserver ni afficher la clé.
        return self.model + ':' + hashlib.sha256(self.api_key.encode()).hexdigest()[:12]

    @staticmethod
    def sdk_installed():
        import importlib.util
        try:
            return importlib.util.find_spec('google.genai') is not None
        except (ImportError, ValueError):
            return False

    def reasons(self):
        reasons = []
        if _flag(self.config.get('PUBLIC_DEMO_MODE')):
            reasons.append('Gemini est désactivé en démonstration publique.')
        if not _flag(self.config.get('GEMINI_ENABLED')):
            reasons.append('Le mode Gemini n’est pas activé (GEMINI_ENABLED=false).')
        if not self.api_key:
            reasons.append('Aucune clé Gemini n’est configurée (variable GEMINI_API_KEY).')
        elif self.api_key.upper() in ('YOUR_API_KEY', 'VOTRE_CLE', '<VOTRE CLÉ>', 'CHANGE_ME', 'XXX'):
            reasons.append('GEMINI_API_KEY contient une valeur d’exemple ou trop courte : collez votre vraie clé dans .env.')
        if not self.sdk_installed():
            reasons.append('Le SDK officiel google-genai n’est pas installé (lancez INSTALLER_WINDOWS.bat).')
        if not _flag(self.config.get('GEMINI_FREE_TIER_CONFIRMED')):
            reasons.append('Le responsable n’a pas confirmé les conditions et quotas de son compte (GEMINI_FREE_TIER_CONFIRMED).')
        if self.model not in allowed_models(self.config):
            reasons.append('Le modèle configuré n’est pas dans la liste autorisée (GEMINI_ALLOWED_MODELS).')
        return reasons

    @property
    def enabled(self):
        return not self.reasons()

    def _usage_file(self):
        private = self.config.get('PRIVATE_DIR')
        return Path(private) / 'gemini_usage.json' if private else None

    def _read_usage(self):
        path = self._usage_file()
        today = date.today().isoformat()
        if path and path.exists():
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                if data.get('day') == today and isinstance(data.get('count'), int):
                    return data
            except (OSError, ValueError):
                pass
        return {'day': today, 'count': 0}

    def _write_usage(self, data):
        path = self._usage_file()
        if not path:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data), encoding='utf-8')
        except OSError:
            logger.warning('Compteur Gemini non enregistré (disque indisponible).')

    def last_verification(self):
        with _STATE_LOCK:
            return dict(_VERIFICATION.get(self._fingerprint()) or {})

    def status(self):
        usage = self._read_usage()
        reasons = self.reasons()
        check = self.last_verification() if not reasons else {}
        verified = bool(check.get('ok'))
        if reasons:
            state, label = 'disabled', 'Gemini indisponible (configuration incomplète)'
        elif verified:
            state, label = 'connected', f"Gemini connecté — test réel réussi ({check['model']}, {check['latency_ms']} ms)"
        elif check:
            state, label = 'error', 'Gemini configuré mais le dernier test réel a échoué : ' + check.get('error_label', 'erreur')
        else:
            state, label = 'configured', 'Gemini configuré — connexion non encore testée'
        return {'enabled': not reasons, 'state': state, 'label': label, 'verified': verified,
                'last_check': check or None, 'model': self.model, 'reasons': reasons,
                'key_present': bool(self.api_key), 'sdk_installed': self.sdk_installed(),
                'daily_limit': self.daily_limit, 'used_today': usage['count'],
                'remaining_today': max(0, self.daily_limit - usage['count']),
                'rate_per_minute': self.rate_per_minute, 'timeout_seconds': self.timeout_ms // 1000}

    def verify_connection(self, client=None):
        """Vraie requête minimale (aucune donnée utilisateur). Résultat conservé en mémoire, sans la clé."""
        import datetime
        started = time.perf_counter()
        result = {'ok': False, 'model': self.model, 'checked_at': datetime.datetime.now().isoformat(timespec='seconds')}
        try:
            text = self._call('verification', 'Réponds uniquement par le mot OK.',
                              {'temperature': 0, 'max_output_tokens': 256}, client=client, allow_empty=True)
            result.update(ok=True, reply_received=bool(text.strip()))
        except GeminiError as exc:
            result.update(error_code=exc.code, error_label=ERROR_LABELS.get(exc.code, 'Erreur Gemini'), message=exc.user_message)
        result['latency_ms'] = int((time.perf_counter() - started) * 1000)
        if result.get('error_code') not in ('disabled', 'rate_limited'):
            with _STATE_LOCK:
                _VERIFICATION[self._fingerprint()] = dict(result)
        return result

    def list_models(self, client=None):
        """Modèles Gemini utilisables en generateContent pour CETTE clé (noms seulement)."""
        owned = client is None
        client = client or self.get_client()
        try:
            names = []
            for model in client.models.list():
                actions = getattr(model, 'supported_actions', None) or []
                name = str(getattr(model, 'name', '')).removeprefix('models/')
                if 'gemini' in name and (not actions or 'generateContent' in actions):
                    names.append(name)
            return sorted(set(names))
        except Exception as exc:  # noqa: BLE001
            raise self.translate_error(exc) from exc
        finally:
            if owned and hasattr(client, 'close'):
                client.close()

    # ------------------------------------------------------------- garde-fous
    def _reserve_call(self):
        """Limitation par minute et quota quotidien, avant tout appel réseau."""
        with _STATE_LOCK:
            moment = time.monotonic()
            while _CALLS and moment - _CALLS[0] > 60:
                _CALLS.popleft()
            if self.rate_per_minute and len(_CALLS) >= self.rate_per_minute:
                raise GeminiRateLimited()
            usage = self._read_usage()
            if self.daily_limit and usage['count'] >= self.daily_limit:
                raise GeminiQuotaExceeded('Quota quotidien local Gemini atteint (%d demandes). La version locale est utilisée.' % self.daily_limit)
            usage['count'] += 1
            self._write_usage(usage)
            _CALLS.append(moment)

    @staticmethod
    def _cache_key(task, model, payload, instruction, schema):
        material = json.dumps([task, model, payload, instruction, schema], sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(material.encode('utf-8')).hexdigest()

    def _cache_get(self, key):
        with _STATE_LOCK:
            item = _CACHE.get(key)
            if not item:
                return None
            if item[0] < time.monotonic():
                _CACHE.pop(key, None)
                return None
            _CACHE.move_to_end(key)
            return item[1]

    def _cache_put(self, key, value):
        if not self.cache_ttl:
            return
        with _STATE_LOCK:
            _CACHE[key] = (time.monotonic() + self.cache_ttl, value)
            _CACHE.move_to_end(key)
            while len(_CACHE) > _CACHE_MAX:
                _CACHE.popitem(last=False)

    # --------------------------------------------------------------- client
    def get_client(self, timeout_ms=None):
        if self.client_factory:
            return self.client_factory()
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # SDK absent : bascule locale
            raise GeminiDisabled('Le SDK officiel google-genai n’est pas installé (pip install -r requirements.txt).') from exc
        return genai.Client(api_key=self.api_key,
                            http_options=types.HttpOptions(timeout=timeout_ms or self.timeout_ms))

    @staticmethod
    def translate_error(exc):
        if isinstance(exc, GeminiError):
            return exc
        code = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
        name = type(exc).__name__.lower()
        text = (name + ' ' + str(exc)).lower()
        if code == 429 or 'resource_exhausted' in text or ' 429' in text:
            return GeminiQuotaExceeded('Quota Gemini du fournisseur atteint (429). La version locale est utilisée.')
        if code in (401, 403) or 'api key not valid' in text or 'api_key_invalid' in text or 'permission_denied' in text \
                or 'unauthenticated' in text:
            return GeminiAuthError()
        if code == 404 or ('not_found' in text and 'model' in text):
            return GeminiModelUnavailable()
        if 'timeout' in name or 'timed out' in text or 'deadline' in text or 'readtimeout' in text:
            return GeminiTimeout()
        network_markers = ('connecterror', 'connectionerror', 'getaddrinfo', 'name or service not known',
                           'failed to establish', 'network is unreachable', 'temporary failure in name resolution',
                           'nodename nor servname', 'no route to host', 'connection refused', 'remotedisconnected',
                           'proxyerror', 'ssl')
        if any(marker in text for marker in network_markers):
            return GeminiNetworkError()
        if isinstance(exc, (ValueError, json.JSONDecodeError)):
            return GeminiInvalidResponse()
        return GeminiError()

    # ---------------------------------------------------------------- appels
    def _call(self, task, contents, request_config, client=None, cache_key=None, allow_empty=False, retry=True):
        if not self.enabled:
            raise GeminiDisabled(' '.join(self.reasons()))
        if cache_key:
            cached = self._cache_get(cache_key)
            if cached is not None:
                logger.info('gemini task=%s model=%s status=cache', task, self.model)
                return cached
        self._reserve_call()
        owned = client is None
        started = time.perf_counter()
        try:
            client = client or self.get_client()
            response = client.models.generate_content(model=self.model, contents=contents, config=request_config)
            text = getattr(response, 'text', None)
            if allow_empty and response is not None:
                text = text if isinstance(text, str) else ''
            elif not isinstance(text, str) or not text.strip():
                raise GeminiInvalidResponse()
            logger.info('gemini task=%s model=%s status=ok duration_ms=%d', task, self.model,
                        int((time.perf_counter() - started) * 1000))
            return text
        except Exception as exc:  # noqa: BLE001 - traduit en erreur métier
            error = self.translate_error(exc)
            http_status = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
            logger.warning('gemini task=%s model=%s status=%s http_status=%s duration_ms=%d',
                           task, self.model, error.code, http_status if type(http_status) is int else '-',
                           int((time.perf_counter() - started) * 1000))
            if retry and http_status in (500, 503) and owned and not self.client_factory:
                time.sleep(1)
                return self._call(task, contents, request_config, cache_key=cache_key,
                                  allow_empty=allow_empty, retry=False)
            raise error from exc
        finally:
            if owned and client is not None and hasattr(client, 'close'):
                try:
                    client.close()
                except Exception:  # noqa: BLE001
                    pass

    def generate_json(self, task, payload, schema, instruction, client=None, temperature=0,
                      max_output_tokens=6000, use_cache=True):
        """Réponse JSON validée par un schéma. Lève GeminiError en cas d'échec."""
        key = self._cache_key(task, self.model, payload, instruction, schema) if use_cache and client is None and not self.client_factory else None
        request_config = {'response_mime_type': 'application/json', 'response_json_schema': schema,
                          'temperature': temperature, 'max_output_tokens': max_output_tokens,
                          'system_instruction': instruction}
        contents = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        text = self._call(task, contents, request_config, client=client, cache_key=key)
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise GeminiInvalidResponse() from exc
        if key:
            self._cache_put(key, text)
        return value

    def generate_text(self, task, payload, instruction, client=None, temperature=0.4,
                      max_output_tokens=2500, use_cache=True):
        key = self._cache_key(task, self.model, payload, instruction, None) if use_cache and client is None and not self.client_factory else None
        request_config = {'temperature': temperature, 'max_output_tokens': max_output_tokens,
                          'system_instruction': instruction}
        contents = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        text = self._call(task, contents, request_config, client=client, cache_key=key)
        if key:
            self._cache_put(key, text)
        return text.strip()


def reset_state_for_tests():
    with _STATE_LOCK:
        _CALLS.clear()
        _CACHE.clear()
        _VERIFICATION.clear()


def service(config, client_factory=None):
    return GeminiService(config, client_factory)
