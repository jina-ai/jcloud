def set_deploy_parser(parser=None):
    if not parser:
        from .base import set_base_parser

        parser = set_base_parser()

    parser.add_argument(
        'path',
        type=str,
        help='The local path to a Jina flow project.',
    )
    parser.add_argument(
        '--name',
        type=str,
        help='If set, the URL of the flow will be prepended with this name',
    )
    parser.add_argument(
        '--workspace',
        type=str,
        help='The string ID of a workspace. If set, re-use the given workspace instead of creating a new one.',
    )
    return parser
