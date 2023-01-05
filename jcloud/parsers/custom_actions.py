from .base import set_base_parser


def set_restart_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        'flow',
        help='The string ID of the flow to be restarted',
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--gateway',
        action='store_true',
        required=False,
        help="to restart only gateway",
    )
    group.add_argument(
        '--executor',
        type=str,
        action='store',
        required=False,
        help="--executor <executorName> : to restart only executor",
    )

    parser.usage = 'jc restart flow [-h] [ --gateway | --executor ]'

    return parser
