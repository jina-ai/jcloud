from .base import set_base_parser


def set_list_parser(parser=None):
    from ..constants import Status

    if not parser:
        parser = set_base_parser()

    parser.add_argument(
        '--status',
        type=str.upper,
        default=Status.ALIVE.value,
        choices=[s.value for s in Status] + ['ALL'],
        help='Pass the status of Flows to be listed.',
    )
    return parser
