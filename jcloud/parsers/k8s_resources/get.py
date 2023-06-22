from ..base import set_base_parser
from ..helper import _chf


def set_get_parser(parser=None):

    if not parser:
        parser = set_base_parser()

    get_subparser = parser.add_subparsers(
        dest='resource',
        help='Subparser to get a Job or Secret.',
        required=True,
    )

    job_parser = get_subparser.add_parser(
        'job',
        help='Get a Job in a Flow.',
        formatter_class=_chf,
    )

    job_parser.add_argument(
        'name',
        type=str,
        help='The name of the Job.',
    )

    job_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )

    secret_parser = get_subparser.add_parser(
        'secret',
        help='Get a Secret in a Flow.',
        formatter_class=_chf,
    )

    secret_parser.add_argument(
        'name',
        type=str,
        help='The name of the Secret.',
    )

    secret_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )

    return parser
