from pathlib import Path


def set_normalize_parser(parser=None):
    if not parser:
        from .base import set_base_parser

        parser = set_base_parser()
    parser.add_argument(
        'path',
        type=Path,
        help='The local path to a Jina Flow project directory or yml file.',
    )
    parser.add_argument(
        '-o',
        '--output',
        type=Path,
        help='The output path to the normalized Jina Flow yml file.',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Increase verbosity.',
    )
    parser.set_defaults(verbose=False)
    return parser
