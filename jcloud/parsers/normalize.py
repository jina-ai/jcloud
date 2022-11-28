from pathlib import Path


def set_normalize_parser(parser=None):
    if not parser:
        from .base import set_base_parser

        parser = set_base_parser()
    parser.add_argument(
        'path',
        type=Path,
        help='The local path to a Jina flow project directory or yml file.',
    )
    return parser
