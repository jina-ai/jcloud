import ast
from pathlib import Path
from ..base import set_base_parser


def set_resource_update_parser(update_subparser=None):
    if not update_subparser:
        parser = set_base_parser()

        update_subparser = parser.add_subparsers(
            dest='resource',
            help='Subparser to update Kubernetes Resources.',
            required=True,
        )

    _set_update_secret_parser(update_subparser)

    return update_subparser


def _set_update_secret_parser(subparser=None):
    if not subparser:
        subparser = set_resource_update_parser()

    secret_update_parser = subparser.add_parser('secret', help='Update a Secret.')

    secret_update_parser.add_argument('name', help='The name of the Secret.')

    secret_update_parser.add_argument(
        '-f',
        '--flow',
        type=str,
        required=True,
        help='The string ID of the Flow.',
    )

    secret_update_parser.add_argument(
        '--from-literal',
        required=True,
        type=ast.literal_eval,
        help='Literal Secret value. Should follow the format "{\'env1\':\'value\'},\'env2\':\'value2\'}}".',
    )

    secret_update_parser.add_argument(
        '--update',
        required=False,
        default=True,
        action='store_true',
        help='Whether to update the flow spec after create the Secret',
    )

    secret_update_parser.add_argument(
        '--path',
        required=False,
        type=Path,
        help='The path of flow yaml spec file',
    )
