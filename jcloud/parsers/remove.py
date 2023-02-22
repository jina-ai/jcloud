from .base import set_base_parser


def set_remove_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    remove_group = parser.add_mutually_exclusive_group()

    remove_group.add_argument(
        '--phase',
        help='The phase to filter flows on for removal',
        type=str,
        default='Failed',
        choices=['Pending', 'Starting', 'Updating', 'Serving', 'Paused', 'Failed'],
    )

    remove_group.add_argument(
        '--flows',
        nargs="*",
        help='The string ID of a flow for single removal, '
        'or a list of space seperated string IDs for multiple removal, '
        'or string \'all\' for deleting ALL SERVING flows.',
    )
    return parser
