from .helper import _chf
from ..constants import Phase, Resources


def set_remove_resource_parser(subparser, parser_prog):

    if Resources.Flow in parser_prog:
        remove_parser = subparser.add_parser(
            'remove',
            help='Remove Flow(s). If `all` is passed it removes Flows in `Serving` or `Failed` phase.',
            formatter_class=_chf,
        )
        _set_remove_flow_parser(remove_parser)
    else:
        resource = Resources.Job if Resources.Job in parser_prog else Resources.Secret
        remove_parser = subparser.add_parser(
            'remove',
            help=f'Remove a {resource.title()} from a Flow.',
            formatter_class=_chf,
        )
        _set_remove_resource_parser(remove_parser, resource)


def _set_remove_flow_parser(remove_parser):
    remove_parser.add_argument(
        '--phase',
        help='The phase to filter flows on for removal',
        type=str,
        choices=[s.value for s in Phase if s.value != ''] + ['All'],
    )

    remove_parser.add_argument(
        'flows',
        nargs="*",
        help='The string ID of a flow for single removal, '
        'or a list of space seperated string IDs for multiple removal, '
        'or string \'all\' for deleting ALL SERVING flows.',
    )


def _set_remove_resource_parser(remove_parser, resource):
    remove_parser.add_argument(
        'name',
        type=str,
        help=f'The name of the {resource.title()} to remove.',
    )

    remove_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )
