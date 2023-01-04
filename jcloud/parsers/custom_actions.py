from .base import set_base_parser


def set_restart_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        'flow',
        help='The string ID of the flow to be restarted',
    )

    return parser
