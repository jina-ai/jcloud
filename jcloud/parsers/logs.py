from .base import set_base_parser


def set_logs_parser(parser=None):

    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        'flow',
        type=str,
        help='The string ID of a flow.',
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        '--gateway',
        action='store_true',
        required=False,
        help='Get logs for gateway',
    )
    group.add_argument(
        '--executor',
        type=str,
        required=False,
        help='Get logs for executor',
    )

    return parser
