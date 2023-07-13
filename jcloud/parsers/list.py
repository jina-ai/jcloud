from .helper import _chf
from ..constants import Phase, Resources


def set_list_resource_parser(subparser, parser_prog):

    if Resources.Flow in parser_prog:
        list_parser = subparser.add_parser(
            'list',
            help='List all Flows that are in `Serving` or `Failed` phase if no phase is passed.',
            formatter_class=_chf,
        )
        _set_list_flow_parser(list_parser)
    else:
        resource = Resources.Job if Resources.Job in parser_prog else Resources.Secret
        list_parser = subparser.add_parser(
            'list',
            help=f'List {resource.title()}s in a Flow.',
            formatter_class=_chf,
        )
        _set_list_resource_parser(list_parser)


def _set_list_flow_parser(list_parser):
    list_parser.add_argument(
        '--phase',
        type=str.title,
        choices=[s.value for s in Phase] + ['All'],
        help='Pass the phase of Flows to be listed.',
    )

    list_parser.add_argument(
        '--name',
        type=str,
        default=None,
        help='Pass the name of Flows to be listed.',
    )

    list_parser.add_argument(
        '--labels',
        type=str,
        default=None,
        help='Pass the labels with which to filter flows. Format is comma separated list of `key=value`.',
    )


def _set_list_resource_parser(list_parser):
    list_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )
