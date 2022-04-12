def set_deploy_parser(parser=None):
    if not parser:
        from .base import set_base_parser

        parser = set_base_parser()

    parser.add_argument(
        'path',
        type=str,
        help='The Jina flow project path.',
    )
    parser.add_argument(
        '--name',
        type=str,
        help='Assign the flow with a customized name.',
    )
    parser.add_argument(
        '--workspace',
        type=str,
        help='If set, re-use the given workspace instead of creating a new one.',
    )
    return parser
