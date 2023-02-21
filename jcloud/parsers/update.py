from .base import set_base_parser
from pathlib import Path


def set_update_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        'flow',
        help='The string ID of the flow to be updated',
    )

    parser.add_argument(
        'path',
        type=Path,
        help='The local path to a Jina flow project directory or yml file.',
    )

    return parser
