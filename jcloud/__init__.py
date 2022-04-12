__version__ = '0.0.0'

import os

WOLF_API = 'https://api.wolf.jina.ai/dev/flows'
LOGSTREAM_API = 'wss://logs.wolf.jina.ai/dev/'
AUTH_HEADERS = {'Authorization': os.environ.get('WOLF_TOKEN', '')}


def main():
    from .parsers import get_main_parser
    from jcloud import api

    args = get_main_parser().parse_args()

    try:
        getattr(api, args.cli.replace('-', '_'))(args)
    except KeyboardInterrupt:
        pass
