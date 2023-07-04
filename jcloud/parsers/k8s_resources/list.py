from ..base import set_base_parser


def set_resource_list_parser(list_subparser=None):
    if not list_subparser:
        parser = set_base_parser()

        list_subparser = parser.add_subparsers(
            dest='resource',
            help='Subparser to list Kubernetes Resources.',
            requried=True,
        )

    _set_list_job_parser(list_subparser)
    _set_list_secret_parser(list_subparser)


def _set_list_job_parser(subparser=None):
    if not subparser:
        subparser = set_resource_list_parser()

    job_list_parser = subparser.add_parser(
        'jobs',
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
        subparser = set_resource_list_parser()

    secret_list_parser = subparser.add_parser(
        'secrets',
        help='List secrets in a Flow.',
    )
    secret_list_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )

    return secret_list_parser
