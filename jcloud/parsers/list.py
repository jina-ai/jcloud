from .base import set_base_parser


def set_list_parser(parser=None):
    from ..constants import Phase

    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        '--status',
        type=str.upper,
        default=Phase.ALIVE.value,
        choices=[s.value for s in Phase] + ['ALL'],
        help='Pass the status of Flows to be listed.',
    )
    return parser
