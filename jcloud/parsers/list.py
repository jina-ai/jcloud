from .base import set_base_parser
from .k8s_resources.list import set_resource_list_parser


def set_list_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    list_subparser = parser.add_subparsers(
        dest='resource',
        help='Subparser to list Flows, Jobs or Secrets',
        required=True,
    )

    _set_list_flow_parser(list_subparser)
    set_resource_list_parser(list_subparser)

    return parser


def _set_list_flow_parser(subparser=None):
    from ..constants import Phase

    if not subparser:
        subparser = set_list_parser()

    flow_list_parser = subparser.add_parser(
        'flows',
        help='List all Flows that are in `Serving` or `Failed` phase if no phase is passed.',
    )
    flow_list_parser.add_argument(
        '--phase',
        type=str.title,
        choices=[s.value for s in Phase] + ['All'],
        help='Pass the phase of Flows to be listed.',
    )

    flow_list_parser.add_argument(
        '--name',
        type=str,
        default=None,
        help='Pass the name of Flows to be listed.',
    )

    flow_list_parser.add_argument(
        '--labels',
        type=str,
        default=None,
        help='Pass the labels with which to filter flows. Format is comma separated list of `key=value`.',
    )

    return flow_list_parser
