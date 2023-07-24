from pathlib import Path
from .helper import _chf


def set_normalize_parser(subparser):
    normalize_parser = subparser.add_parser(
        'normalize',
        help='Normalize a Flow.',
        formatter_class=_chf,
    )
    normalize_parser.add_argument(
        'path',
        type=Path,
        help='The local path to a Jina Flow project directory or yml file.',
    )
    normalize_parser.add_argument(
        '-o',
        '--output',
        type=Path,
        help='The output path to the normalized Jina Flow yml file.',
    )
    normalize_parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Increase verbosity.',
    )
    normalize_parser.set_defaults(verbose=False)
