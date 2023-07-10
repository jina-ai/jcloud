from .helper import _chf
from ..constants import Resources


def set_logs_resource_parser(subparser, parser_prog):

    if Resources.Flow in parser_prog:
        logs_parser = subparser.add_parser(
            'logs',
            help='Get logs of a Flow gateway or executor.',
            formatter_class=_chf,
        )
        _set_logs_flow_parser(logs_parser)
    else:
        logs_parser = subparser.add_parser(
            'logs',
            help='Get logs of a Job.',
            formatter_class=_chf,
        )
        _set_logs_job_parser(logs_parser)


def _set_logs_flow_parser(logs_parser):
    logs_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of a Flow.',
    )

    group = logs_parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        '--gateway',
        action='store_true',
        required=False,
        help='Get logs for gateway.',
    )
    group.add_argument(
        '--executor',
        type=str,
        required=False,
        help='Get logs for executor.',
    )


def _set_logs_job_parser(logs_parser):
    logs_parser.add_argument(
        'name',
        type=str,
        help='The name of the Job.',
    )

    logs_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of a Flow.',
    )
