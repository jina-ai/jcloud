from .base import set_base_parser


def set_list_parser(parser=None):
    from ..constants import Phase

    if not parser:
        parser = set_base_parser()

    list_subparser = parser.add_subparsers(
        dest='resource',
        help='Subparser to list Flows, Jobs or Secrets',
        required=True,
    )

    flow_list_parser = list_subparser.add_parser(
        'flow',
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

    job_list_parser = list_subparser.add_parser(
        'job',
        help='List jobs in a Flow.',
    )
    job_list_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )

    secret_list_parser = list_subparser.add_parser(
        'secret',
        help='List secrets in a Flow.',
    )
    secret_list_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )

    return parser
