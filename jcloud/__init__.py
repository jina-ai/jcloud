__version__ = '0.0.2'

WOLF_API = 'https://api.wolf.jina.ai/dev/flows'
LOGSTREAM_API = 'wss://logs.wolf.jina.ai/dev/'


def main():
    from .parsers import get_main_parser

    args = get_main_parser().parse_args()

    if args.loglevel:
        import os

        os.environ['JCLOUD_LOGLEVEL'] = args.loglevel

    try:
        from jcloud import api

        getattr(api, args.cli.replace('-', '_'))(args)
    except KeyboardInterrupt:
        pass
