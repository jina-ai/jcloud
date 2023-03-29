from .base import set_base_parser


def set_list_parser(parser=None):
    from ..constants import Phase

    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        '--phase',
        type=str.title,
        choices=[s.value for s in Phase] + ['All'],
        help='Pass the phase of Flows to be listed.',
    )

    parser.add_argument(
        '--name',
        type=str,
        default=None,
        help='Pass the name of Flows to be listed.',
    )

    parser.add_argument(
        '--labels',
        type=str,
        default=None,
        help='Pass the labels with which to filter flows. Format is comma separated list of `key=value`.',
    )
    return parser
