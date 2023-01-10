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


def set_pause_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        'flow',
        help='The string ID of the flow to be paused',
    )

    return parser


def set_resume_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        'flow',
        help='The string ID of the flow to be resumed',
    )

    return parser


def set_scale_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        'flow',
        help='The string ID of the flow to be resumed',
    )

    parser.add_argument(
        '--executor',
        type=str,
        required=True,
        help='The name of the executor to scale',
    )

    def validate_replicas(val):
        val = int(val)
        if val <= 0:
            raise ValueError(
                f'invalid count. replicas must be greater than 0, got: {val}'
            )
        return val

    parser.add_argument(
        '--replicas',
        type=validate_replicas,
        required=True,
        help='The name of the executor to scale',
    )
