from .base import set_base_parser


def set_login_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        '-f',
        '--force',
        action='store_true',
        default=False,
        help='Force to login.',
    )
    return parser
