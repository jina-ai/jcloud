import ast
from pathlib import Path

from ..base import set_base_parser
from ..helper import _chf


def set_create_parser(parser=None):

    if not parser:
        parser = set_base_parser()

    create_subparser = parser.add_subparsers(
        dest='resource',
        help='Subparser to create a Job or a Secret.',
        required=True,
    )

    _set_create_job_parser(create_subparser)
    _set_create_secret_parser(create_subparser)

    return parser


def _set_create_job_parser(subparser=None):

    if not subparser:
        subparser = set_create_parser()

    job_parser = subparser.add_parser(
        'job',
        help='Create a Job for a Flow.',
        formatter_class=_chf,
    )

    job_parser.add_argument(
        'name',
        type=str,
        help='The name of the Job.',
    )

    job_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )

    job_parser.add_argument(
        'image',
        type=str,
        help='The image the Job will use.',
    )

    job_parser.add_argument(
        '--timeout',
        type=int,
        help='Duration the Job will be active before termination.',
    )

    job_parser.add_argument(
        '--backofflimit',
        type=int,
        help='Number of retries before Job is marked as failed.',
    )

    job_parser.add_argument(
        'entrypoint',
        type=str,
        help='The command to be added to the image\'s entrypoint.',
    )

    return subparser


def _set_create_secret_parser(subparser=None):

    if not subparser:
        subparser = set_create_parser()

    secret_parser = subparser.add_parser(
        'secret',
        help='Create a Secret for a Flow.',
        formatter_class=_chf,
    )

    secret_parser.add_argument(
        'name',
        type=str,
        help='The name of the Secret.',
    )

    secret_parser.add_argument(
        '-f',
        '--flow',
        type=str,
        required=True,
        help='The string ID of the Flow.',
    )

    secret_parser.add_argument(
        '--from-literal',
        required=True,
        type=ast.literal_eval,
        help='Literal Secret value. Should follow the format "{\'env1\':\'value\'},\'env2\':\'value2\'}".',
    )

    secret_parser.add_argument(
        '--update',
        required=False,
        action='store_true',
        help='Whether to update the flow spec after create the Secret',
    )

    secret_parser.add_argument(
        '--path',
        required=False,
        type=Path,
        help='The path of flow yaml spec file',
    )

    return subparser
