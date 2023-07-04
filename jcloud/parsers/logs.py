from .base import set_base_parser
from .helper import _chf


def set_logs_parser(parser=None):

    if not parser:
        parser = set_base_parser()

    logs_subparser = parser.add_subparsers(
        dest='resource',
        help='Subparser to get logs of a Flow or Job.',
        required=True,
    )

    flow_logs_parser = logs_subparser.add_parser(
        'flow',
        help='Get logs of a Flow gateway or executor.',
        formatter_class=_chf,
    )

    flow_logs_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of a Flow.',
    )

    group = flow_logs_parser.add_mutually_exclusive_group(required=True)

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

    job_logs_parser = logs_subparser.add_parser(
        'job',
        help='Get logs of a Job.',
        formatter_class=_chf,
    )

    job_logs_parser.add_argument(
        '-f',
        '--flow',
        type=str,
        required=True,
        help='The string ID of a Flow.',
    )

    job_logs_parser.add_argument(
        'name',
        type=str,
        help='The name of the Job.',
    )

    return parser
