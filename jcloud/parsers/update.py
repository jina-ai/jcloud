import ast
from pathlib import Path

from .helper import _chf
from ..constants import Resources


def set_update_resource_parser(subparser, parser_prog):

    if Resources.Flow in parser_prog:
        update_parser = subparser.add_parser(
            'update',
            help='Update a Flow.',
            formatter_class=_chf,
        )
        _set_update_flow_parser(update_parser)
    else:
        update_parser = subparser.add_parser(
            'update',
            help='Update a Secret.',
            formatter_class=_chf,
        )
        _set_update_secret_parser(update_parser)


def _set_update_flow_parser(update_parser):
    update_parser.add_argument(
        'flow',
        help='The string ID of the flow to be updated',
    )

    update_parser.add_argument(
        'path',
        type=Path,
        help='The local path to a Jina flow project directory or yml file.',
    )


def _set_update_secret_parser(update_parser):
    update_parser.add_argument(
        'name',
        help='The name of the Secret.',
    )

    update_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )

    update_parser.add_argument(
        '--from-literal',
        type=ast.literal_eval,
        help='Literal Secret value. Should follow the format "{\'env1\':\'value\'},\'env2\':\'value2\'}}".',
    )

    update_parser.add_argument(
        '--update',
        action='store_true',
        help='Whether to update the flow spec after create the Secret',
    )

    update_parser.add_argument(
        '--path',
        type=Path,
        help='The path of flow yaml spec file',
    )
