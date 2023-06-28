from .base import set_base_parser
from pathlib import Path


def set_update_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    update_subparser = parser.add_subparsers(
        dest='resource',
        help='Subparser to update a Flow or Secret.',
        required=True,
    )

    flow_update_parser = update_subparser.add_parser('flow', help='Update a Flow.')

    flow_update_parser.add_argument(
        'flow',
        help='The string ID of the flow to be updated',
    )

    flow_update_parser.add_argument(
        'path',
        type=Path,
        help='The local path to a Jina flow project directory or yml file.',
    )

    secret_update_parser = update_subparser.add_parser(
        'secret', help='Update a Secret.'
    )

    secret_update_parser.add_argument('name', help='The name of the Secret.')

    secret_update_parser.add_argument(
        '--from-literal',
        type=str,
        help='Literal Secret value.',
    )

    return parser
