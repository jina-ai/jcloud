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

    job_parser = create_subparser.add_parser(
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
        'image-name',
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

    secret_parser = create_subparser.add_parser(
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
        'path',
        type=Path,
        help='The local path to a Jina flow project directory or yml file.',
    )

    secret_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )

    secret_parser.add_argument(
        '--executor',
        type=str,
        help='The executor to which the Secret will be added.',
    )

    secret_parser.add_argument(
        '--from-literal',
        type=ast.literal_eval,
        help='Literal Secret value. Should follow the format "{\'env1\':{\'key\':\'value\'},\'env2\'{\'key2\':\'value2\'}}".',
    )

    return parser
