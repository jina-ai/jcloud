from .base import set_base_parser


def set_list_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    list_subparser = parser.add_subparsers(
        dest='resource',
        help='Subparser to list Flows, Jobs or Secrets',
        required=True,
    )

    _set_list_flow_parser(list_subparser)
    _set_list_job_parser(list_subparser)
    _set_list_secret_parser(list_subparser)

    return parser


def _set_list_flow_parser(subparser=None):
    from ..constants import Phase

    if not subparser:
        subparser = set_list_parser()

    flow_list_parser = subparser.add_parser(
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

    return flow_list_parser


def _set_list_job_parser(subparser=None):
    if not subparser:
        subparser = set_list_parser()

    job_list_parser = subparser.add_parser(
        'job',
        help='List jobs in a Flow.',
    )
    job_list_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )

    return job_list_parser


def _set_list_secret_parser(subparser=None):
    if not subparser:
        subparser = set_list_parser()

    secret_list_parser = subparser.add_parser(
        'secret',
        help='List secrets in a Flow.',
    )
    secret_list_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )

    return secret_list_parser
