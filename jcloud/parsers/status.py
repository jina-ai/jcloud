from .helper import _chf


def set_status_parser(subparser):
    status_parser = subparser.add_parser(
        'status',
        help='Get the status of a Flow.',
        formatter_class=_chf,
    )

    status_parser.add_argument(
        'flow',
        type=str,
        help='The string ID of a flow.',
    )

    status_parser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='Pass if you want to see the full details of the Flow.',
    )
