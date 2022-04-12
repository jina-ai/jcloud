def get_main_parser():
    """The main parser for Jina

    :return: the parser
    """
    from .base import set_base_parser, set_simple_parser
    from .deploy import set_deploy_parser
    from .helper import _chf

    # create the top-level parser
    parser = set_base_parser()

    sp = parser.add_subparsers(
        dest='cli',
        required=True,
    )

    set_deploy_parser(
        sp.add_parser(
            'deploy',
            help='Deploy a flow',
            formatter_class=_chf,
        )
    )

    sp.add_parser(
        'list',
        help='List all flows',
        formatter_class=_chf,
    )

    set_simple_parser(
        sp.add_parser(
            'logs',
            help='Stream logs for a flow',
            formatter_class=_chf,
        )
    )

    set_simple_parser(
        sp.add_parser(
            'status',
            help='Get the status of a flow',
            formatter_class=_chf,
        )
    )

    set_simple_parser(
        sp.add_parser(
            'remove',
            help='Remove a flow',
            formatter_class=_chf,
        )
    )
    #
    # set_new_parser(
    #     sp.add_parser(
    #         'new',
    #         help='Create a new Jina project',
    #         description='Create a new Jina project with the predefined template.',
    #         formatter_class=_chf,
    #     )
    # )

    sp.add_parser(
        'login',
        help='Login to Jina Cloud',
        formatter_class=_chf,
    )

    return parser
