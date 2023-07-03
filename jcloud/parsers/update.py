from .base import set_base_parser
from pathlib import Path
from .k8s_resources.update import set_resource_update_parser


def set_update_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    update_subparser = parser.add_subparsers(
        dest='resource',
        help='Subparser to update a Flow.',
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

    set_resource_update_parser(update_subparser)

    return parser
