from .helper import _chf


def set_restart_parser(subparser):
    restart_parser = subparser.add_parser(
        'restart',
        help='Restart a Flow, executor or gateway.',
        formatter_class=_chf,
    )

    group = restart_parser.add_mutually_exclusive_group()
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

    restart_parser.usage = 'jc flow restart [-h] [ --gateway | --executor ]'


def set_pause_parser(subparser):
    pause_parser = subparser.add_parser(
        'pause',
        help='Pause a Flow.',
        formatter_class=_chf,
    )
    pause_parser.add_argument(
        'flow',
        help='The string ID of the flow to be paused',
    )


def set_resume_parser(subparser):
    resume_parser = subparser.add_parser(
        'resume',
        help='Resume a paused Flow.',
        formatter_class=_chf,
    )
    resume_parser.add_argument(
        'flow',
        help='The string ID of the flow to be resumed',
    )


def set_scale_parser(subparser):
    scale_parser = subparser.add_parser(
        'scale',
        help='Scale executor of a Flow.',
        formatter_class=_chf,
    )

    scale_parser.add_argument(
        'flow',
        help='The string ID of the flow to scale',
    )

    scale_parser.add_argument(
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

    scale_parser.add_argument(
        '--replicas',
        type=validate_replicas,
        required=True,
        help='The name of the executor to scale',
    )


def set_recreate_parser(subparser):
    recreate_parser = subparser.add_parser(
        'recreate',
        help='Recreate deleted Flow',
        formatter_class=_chf,
    )

    recreate_parser.add_argument(
        'flow',
        help='The string ID of the flow to be recreated',
    )
