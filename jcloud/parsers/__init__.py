def get_main_parser():
    """The main parser for Jina

    :return: the parser
    """
    from .base import set_base_parser, set_new_project_parser, set_simple_parser
    from .deploy import set_deploy_parser
    from .helper import _chf
    from .list import set_list_parser
    from .logs import set_logs_parser

    # create the top-level parser
    parser = set_base_parser()

    sp = parser.add_subparsers(
        dest='cli',
        required=True,
    )

    sp.add_parser(
        'login',
        help='Login to Jina Cloud',
        formatter_class=_chf,
    )

    set_deploy_parser(
        sp.add_parser(
            'deploy',
            help='Deploy a Flow',
            formatter_class=_chf,
        )
    )

    set_list_parser(
        sp.add_parser(
            'list',
            help='List all Flows',
            formatter_class=_chf,
        )
    )

    set_logs_parser(
        sp.add_parser(
            'logs',
            help='Stream logs for a Flow',
            formatter_class=_chf,
        )
    )

    set_simple_parser(
        sp.add_parser(
            'status',
            help='Get the status of a Flow',
            formatter_class=_chf,
        )
    )

    set_simple_parser(
        sp.add_parser(
            'remove',
            help='Remove a Flow',
            formatter_class=_chf,
        )
    )

    set_new_project_parser(
        sp.add_parser(
            'new',
            help='Create a new project',
            description='Create a new Jina project via template.',
            formatter_class=_chf,
        )
    )

    sp.add_parser(
        'survey',
        help='Tell us your experience and help us improve',
        formatter_class=_chf,
    )

    return parser
