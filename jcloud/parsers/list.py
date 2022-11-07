from .base import set_base_parser


def set_list_parser(parser=None):
    from ..constants import Phase

    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        '--phase',
        type=str.title,
        default=Phase.Serving.value,
        choices=[s.value for s in Phase] + ['All'],
        help='Pass the phase of Flows to be listed.',
    )

    parser.add_argument(
        '--name',
        type=str,
        default=None,
        help='Pass the name of Flows to be listed.',
    )
    return parser
