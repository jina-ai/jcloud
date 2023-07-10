from .helper import _chf


def set_get_parser(subparser, resource):
    get_parser = subparser.add_parser(
        'get',
        help=f'Get a {resource.title()}.',
        formatter_class=_chf,
    )

    get_parser.add_argument(
        'name',
        type=str,
        help='The name of the Job.',
    )

    get_parser.add_argument(
        '-f',
        '--flow',
        type=str,
        help='The string ID of the Flow.',
    )
