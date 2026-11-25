"""One public WSGI application for hosts that provide a single worker."""
from urllib.parse import urlsplit

import requests
from werkzeug.test import Client

from .app import create_app as create_gateway
from .config import load_config
from .hosted import preflight
from .proxy import BackendTunnel


class WsgiTransport:
    """Dispatch gateway calls directly to the private WSGI app, without a socket."""

    def __init__(self, app, origin):
        self.client = Client(app)
        self.origin = origin

    def post(self, url, *, json, headers, timeout):
        return self.request('POST', url, json=json, headers=headers, timeout=timeout)

    def request(self, method, url, *, headers, timeout, allow_redirects=False, **payload):
        target = urlsplit(url)
        if f'{target.scheme}://{target.netloc}' != self.origin or allow_redirects:
            raise RuntimeError('Requête WSGI interne hors du backend privé.')
        response = self.client.open(path=target.path, query_string=target.query,
                                    base_url=self.origin, method=method, headers=headers,
                                    environ_overrides={'REMOTE_ADDR': '127.0.0.1'},
                                    buffered=True, **payload)
        result = requests.Response()
        result.status_code = response.status_code
        result.headers.update(response.headers)
        result._content = response.get_data()
        return result


def create_application():
    config = load_config()
    preflight(config)
    from backend.web import create_app as create_backend

    backend = create_backend({'TRUST_PROXY': False, 'SESSION_COOKIE_SECURE': False})
    origin = config['AUTH_BACKEND_URL']
    tunnel = BackendTunnel(origin, config['AUTH_PROFILE'], config['AUTH_INTERNAL_SECRET'],
                           transport=WsgiTransport(backend, origin))
    return create_gateway({'AUTH_BACKEND_TUNNEL': tunnel})
