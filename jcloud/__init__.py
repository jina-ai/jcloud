__version__ = '0.0.0'

import os

WOLF_API = 'https://api.wolf.jina.ai/dev/flows'
LOGSTREAM_API = 'wss://logs.wolf.jina.ai/dev/'
ARTIFACT_API = 'https://apihubble.staging.jina.ai/v2/rpc/artifact.upload'
AUTH_HEADERS = {'Authorization': os.environ.get('WOLF_TOKEN', '')}
ARTIFACT_AUTH_HEADERS = {
    'Authorization': f'token {os.environ.get("ARTIFACT_TOKEN", "")}'
}


def main():
    from jcloud import api

    from .parsers import get_main_parser

    args = get_main_parser().parse_args()

    getattr(api, args.cli.replace('-', '_'))(args)
