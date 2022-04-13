import json
import os
import webbrowser
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict
from urllib.parse import parse_qs
from urllib.request import Request, urlopen

import aiohttp

from .helper import get_logger
from rich import print

logger = get_logger()

JINA_CLOUD_CONFIG = 'config.json'


def _get_hub_config() -> Dict:
    hub_root = Path(os.environ.get('JINA_HUB_ROOT', Path.home().joinpath('.jina')))

    if not hub_root.exists():
        hub_root.mkdir(parents=True, exist_ok=True)

    config_file = hub_root.joinpath(JINA_CLOUD_CONFIG)
    if config_file.exists():
        with open(config_file) as f:
            return json.load(f)

    return {}


def _save_hub_config(config: Dict):
    hub_root = Path(os.environ.get('JINA_HUB_ROOT', Path.home().joinpath('.jina')))

    if not hub_root.exists():
        hub_root.mkdir(parents=True, exist_ok=True)

    config_file = hub_root.joinpath(JINA_CLOUD_CONFIG)
    with open(config_file, 'w') as f:
        json.dump(config, f)


@lru_cache()
def _get_cloud_api_url() -> str:
    """Get Cloud Api for transmiting data to the cloud.

    :raises RuntimeError: Encounter error when fetching the cloud Api Url.
    :return: Cloud Api Url
    """
    if 'JINA_HUBBLE_REGISTRY' in os.environ:
        return os.environ['JINA_HUBBLE_REGISTRY']
    else:
        try:
            req = Request(
                'https://api.jina.ai/hub/hubble.json',
                headers={'User-Agent': 'Mozilla/5.0'},
            )
            with urlopen(req) as resp:
                return json.load(resp)['url']
        except Exception as ex:
            logger.error(f'can not get hubble URL due to {ex!r}')


class Auth:
    @staticmethod
    def get_auth_token():
        config = _get_hub_config()
        return config.get('auth_token')

    @staticmethod
    async def login():
        api_host = _get_cloud_api_url()

        async with aiohttp.ClientSession() as session:
            redirect_url = 'http://localhost:8085'

            # TODO: add "app" parameter to API call
            async with session.get(
                url=f'{api_host}/v2/rpc/user.identity.authorize?provider=jina-login&redirectUri={redirect_url}'
            ) as response:
                response.raise_for_status()
                json_response = await response.json()
                logger.debug(json_response)
                webbrowser.open(json_response['data']['redirectTo'], new=2)

        done = False
        post_data = None

        class S(BaseHTTPRequestHandler):
            def _set_response(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

            def do_POST(self):
                nonlocal done, post_data

                content_length = int(self.headers['Content-Length'])
                post_data = parse_qs(self.rfile.read(content_length))

                self._set_response()
                self.wfile.write(
                    'You have successfully logged in! You can close this window now.'.encode(
                        'utf-8'
                    )
                )
                done = True

            def log_message(self, format, *args):
                return

        server_address = ('', 8085)
        with HTTPServer(server_address, S) as httpd:
            logger.debug('Starting httpd...')
            while not done:
                httpd.handle_request()

        logger.debug(post_data)
        logger.debug('Stopping httpd...')

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f'{api_host}/v2/rpc/user.identity.grant.auth0Unified',
                data=post_data,
            ) as response:
                response.raise_for_status()
                json_response = await response.json()
                logger.debug(json_response)
                # TODO: token will expire in 7 days but we need more time.
                token = json_response['data']['token']

        config = _get_hub_config()
        config['auth_token'] = token
        _save_hub_config(config)
        logger.debug('DONE')
        print('[green]:lock: You have successfully logged in![/green]')
