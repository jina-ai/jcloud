from .helper import _chf
from ..constants import Resources


def set_restart_parser(subparser, parser_prog):
    if Resources.Flow in parser_prog:
        set_flow_restart_parser(subparser)
    elif Resources.Deployment in parser_prog:
        set_deployment_restart_parser(subparser)


def set_flow_restart_parser(subparser):
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


def set_deployment_restart_parser(subparser):
    restart_parser = subparser.add_parser(
        "restart",
        help='Restart a Deployment',
        formatter_class=_chf,
    )
    restart_parser.add_argument(
        'deployment', help='The string ID of the Deployment to be restarted'
    )


def set_pause_parser(subparser, parser_prog):
    if Resources.Flow in parser_prog:
        set_flow_pause_parser(subparser)
    elif Resources.Deployment in parser_prog:
        set_deployment_pause_parser(subparser)


def set_flow_pause_parser(subparser):
    pause_parser = subparser.add_parser(
        'pause',
        help='Pause a Flow.',
        formatter_class=_chf,
    )
    pause_parser.add_argument(
        'flow',
        help='The string ID of the flow to be paused',
    )


def set_deployment_pause_parser(subparser):
    pause_parser = subparser.add_parser(
        'pause',
        help='Pause a Deployment.',
        formatter_class=_chf,
    )
    pause_parser.add_argument(
        'deployment',
        help='The string ID of the deployment to be paused',
    )


def set_resume_parser(subparser, parser_prog):
    if Resources.Flow in parser_prog:
        set_flow_resume_parser(subparser)
    elif Resources.Deployment in parser_prog:
        set_deployment_resume_parser(subparser)


def set_flow_resume_parser(subparser):
    resume_parser = subparser.add_parser(
        'resume',
        help='Resume a paused Flow.',
        formatter_class=_chf,
    )
    resume_parser.add_argument(
        'flow',
        help='The string ID of the flow to be resumed',
    )


def set_deployment_resume_parser(subparser):
    resume_parser = subparser.add_parser(
        'resume',
        help='Resume a paused Deployment.',
        formatter_class=_chf,
    )
    resume_parser.add_argument(
        'deployment',
        help='The string ID of the deployment to be resumed',
    )


def set_scale_parser(subparser, parser_prog):
    if Resources.Flow in parser_prog:
        set_flow_scale_parser(subparser)
    elif Resources.Deployment in parser_prog:
        set_deployment_scale_parser(subparser)


def set_flow_scale_parser(subparser):
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
        help='The number of replicas to scale to',
    )


def set_deployment_scale_parser(subparser):
    scale_parser = subparser.add_parser(
        'scale',
        help='Scale executor of a Deployment.',
        formatter_class=_chf,
    )

    scale_parser.add_argument(
        'deployment',
        help='The string ID of the deployment to scale',
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
        help='The number of replicas to scale to',
    )


def set_recreate_parser(subparser, parser_prog):
    if Resources.Flow in parser_prog:
        set_flow_recreate_parser(subparser)
    elif Resources.Deployment in parser_prog:
        set_deployment_recreate_parser(subparser)


def set_flow_recreate_parser(subparser):
    recreate_parser = subparser.add_parser(
        'recreate',
        help='Recreate deleted Flow',
        formatter_class=_chf,
    )

    recreate_parser.add_argument(
        'flow',
        help='The string ID of the flow to be recreated',
    )


def set_deployment_recreate_parser(subparser):
    recreate_parser = subparser.add_parser(
        'recreate',
        help='Recreate deleted Deployment',
        formatter_class=_chf,
    )

    recreate_parser.add_argument(
        'deployment',
        help='The string ID of the deployment to be recreated',
    )
