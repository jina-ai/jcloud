from .helper import _chf
from ..constants import Resources


def set_status_parser(subparser, parser_prog):
    if Resources.Flow in parser_prog:
        set_flow_status_parser(subparser)
    elif Resources.Deployment in parser_prog:
        set_deployment_status_parser(subparser)


def set_flow_status_parser(subparser):
    status_parser = subparser.add_parser(
        'status',
        help='Get the status of a Flow.',
        formatter_class=_chf,
    )

    status_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of a flow.',
    )

    status_parser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='Pass if you want to see the full details of the Flow.',
    )


def set_deployment_status_parser(subparser):
    status_parser = subparser.add_parser(
        'status',
        help='Get the status of a Deployment.',
        formatter_class=_chf,
    )

    status_parser.add_argument(
        'deployment',
        type=str,
        help='The string ID of a deployment.',
    )

    status_parser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='Pass if you want to see the full details of the Deployment.',
    )
