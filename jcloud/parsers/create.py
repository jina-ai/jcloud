import ast

from pathlib import Path

from .helper import _chf
from ..constants import Resources


def set_create_resource_parser(subparser, resource):

    create_parser = subparser.add_parser(
        'create',
        help=f'Create a {resource.title()}.',
        formatter_class=_chf,
    )

    create_parser.add_argument(
        'name',
        type=str,
        help='The name of the Job.',
    )

    create_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )
    if resource == Resources.Job:
        _set_job_create_parser(create_parser)
    else:
        _set_secret_create_parser(create_parser)


def _set_job_create_parser(create_parser):
    create_parser.add_argument(
        'image',
        type=str,
        help='The image the Job will use.',
    )

    create_parser.add_argument(
        'entrypoint',
        type=str,
        help='The command to be added to the image\'s entrypoint.',
    )

    create_parser.add_argument(
        '--timeout',
        type=int,
        default=600,
        help='Duration the Job will be active before termination in seconds.',
    )

    create_parser.add_argument(
        '--backofflimit',
        type=int,
        help='Number of retries before Job is marked as failed.',
    )


def _set_secret_create_parser(create_parser):
    create_parser.add_argument(
        '--from-literal',
        type=ast.literal_eval,
        help='Literal Secret value. Should follow the format "{\'env1\':\'value\'},\'env2\':\'value2\'}".',
    )

    create_parser.add_argument(
        '--update',
        action='store_true',
        help='Whether to update the flow spec after create the Secret',
    )

    create_parser.add_argument(
        '--path',
        type=Path,
        help='The path of flow yaml spec file',
    )
