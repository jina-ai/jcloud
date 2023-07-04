from ..base import set_base_parser


def set_resource_remove_parser(remove_subparser=None):

    if not remove_subparser:
        parser = set_base_parser()

        remove_subparser = parser.add_subparsers(
            dest='resource',
            help='Subparser to remove Kubernetes Resources.',
            required=True,
        )

    _set_remove_job_parser(remove_subparser)
    _set_remove_secret_parser(remove_subparser)


def _set_remove_job_parser(subparser=None):

    if not subparser:
        subparser = set_resource_remove_parser()

    job_remove_parser = subparser.add_parser(
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


def _set_remove_secret_parser(subparser=None):

    if not subparser:
        subparser = set_resource_remove_parser()

    secret_remove_parser = subparser.add_parser(
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
