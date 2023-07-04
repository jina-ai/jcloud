from .base import set_base_parser
from .k8s_resources.remove import set_resource_remove_parser


def set_remove_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    remove_subparser = parser.add_subparsers(
        dest='resource',
        help='Subparser to remove Flows, a Job or a Secret.',
        required=True,
    )

    _set_remove_flow_parser(remove_subparser)
    set_resource_remove_parser(remove_subparser)

    return parser


def _set_remove_flow_parser(subparser=None):

    if not subparser:
        subparser = set_remove_parser()

    flow_remove_parser = subparser.add_parser(
        'flow',
        help='Remove Flow(s). If `all` is passed it removes Flows in `Serving` or `Failed` phase.',
    )
    flow_remove_parser.add_argument(
        '--phase',
        help='The phase to filter flows on for removal',
        type=str,
        choices=['Pending', 'Starting', 'Updating', 'Serving', 'Paused', 'Failed'],
    )

    flow_remove_parser.add_argument(
        'flows',
        nargs="*",
        help='The string ID of a flow for single removal, '
        'or a list of space seperated string IDs for multiple removal, '
        'or string \'all\' for deleting ALL SERVING flows.',
    )

    return flow_remove_parser
