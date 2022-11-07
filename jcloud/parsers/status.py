from .base import set_base_parser


def set_status_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        'flow',
        type=str,
        help='The string ID of a flow.',
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='Pass if you want to see the full details of the Flow.',
    )
    return parser
