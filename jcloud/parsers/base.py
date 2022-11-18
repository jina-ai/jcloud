import argparse


def set_base_parser(parser=None):
    import os

    from .. import __version__
    from .helper import _chf, colored

    if not parser:
        parser = argparse.ArgumentParser(
            description=f'JCloud (v{colored(__version__, "green")}) deploys your Jina Flow to the cloud.',
            formatter_class=_chf,
        )
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version=__version__,
        help='Show version.',
    )
    parser.add_argument(
        '--loglevel',
        type=str,
        choices=['DEBUG', 'INFO', 'CRITICAL', 'NOTSET'],
        default=os.environ.get('JCLOUD_LOGLEVEL', 'INFO'),
        help='Set the loglevel of the logger',
    )
    return parser


def set_simple_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        'flow',
        type=str,
        help='The string ID of a flow.',
    )
    return parser


def set_new_project_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        'path',
        type=str,
        nargs='?',
        help='The new project will be created at this path.',
        default='helloworld',
    )
    return parser
