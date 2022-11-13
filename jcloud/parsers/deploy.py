def set_deploy_parser(parser=None):
    if not parser:
        from .base import set_base_parser

        parser = set_base_parser()

    parser.add_argument(
        'path',
        type=str,
        help='The local path to a Jina flow project.',
    )
    return parser
