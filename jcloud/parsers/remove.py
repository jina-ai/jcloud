from .base import set_base_parser


def set_remove_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    remove_subparser = parser.add_subparsers(
        dest='resource',
        help='Subparser to remove Flows, a Job or a Secret.',
        required=True,
    )

    flow_remove_parser = remove_subparser.add_parser(
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

    job_remove_parser = remove_subparser.add_parser(
        'job',
        help='Remove a Job from a Flow.',
    )
    job_remove_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )
    job_remove_parser.add_argument(
        'name',
        type=str,
        help='The name of the Job to remove.',
    )

    secret_remove_parser = remove_subparser.add_parser(
        'secret',
        help='Remove a Secret from a Flow.',
    )
    secret_remove_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )
    secret_remove_parser.add_argument(
        'name',
        type=str,
        help='The name of the Secret to remove.',
    )
    return parser
