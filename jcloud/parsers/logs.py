from .base import set_base_parser


def set_logs_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        'flow',
        type=str,
        help='The string ID of a flow.',
    )

    parser.add_argument(
        '--executor',
        type=str,
        default=None,
        help='Pass name of the Executor to stream logs from.',
    )
    return parser
