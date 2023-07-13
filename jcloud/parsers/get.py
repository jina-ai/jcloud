from .helper import _chf


def set_get_resource_parser(subparser, resource):
    get_parser = subparser.add_parser(
        'get',
        help=f'Get the details of a {resource.title()}.',
        formatter_class=_chf,
    )

    get_parser.add_argument(
        'name',
        type=str,
        help=f'The name of the {resource.title()}.',
    )

    get_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of the Flow.',
    )
