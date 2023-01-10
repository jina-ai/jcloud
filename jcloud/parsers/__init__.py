def get_main_parser(parser=None):
    """The main parser for Jina

    :return: the parser
    """
    from .base import set_base_parser, set_new_project_parser, set_simple_parser
    from .deploy import set_deploy_parser
    from .helper import _chf
    from .list import set_list_parser
    from .remove import set_remove_parser
    from .status import set_status_parser
    from .normalize import set_normalize_parser
    from .update import set_update_parser
    from .custom_actions import (
        set_restart_parser,
        set_pause_parser,
        set_resume_parser,
        set_scale_parser,
    )

    # create the top-level parser
    parser = set_base_parser(parser=parser)

    sp = parser.add_subparsers(
        dest='jc_cli',
        required=True,
    )

    sp.add_parser(
        'login',
        help='Login to Jina Cloud / Ecosystem.',
        formatter_class=_chf,
    )

    sp.add_parser(
        'logout',
        help='Logout from Jina Cloud / Ecosystem.',
        formatter_class=_chf,
    )

    set_deploy_parser(
        sp.add_parser(
            'deploy',
            help='Deploy a Flow.',
            formatter_class=_chf,
        )
    )

    set_normalize_parser(
        sp.add_parser(
            'normalize',
            help='Normalize a Flow.',
            formatter_class=_chf,
        )
    )

    set_list_parser(
        sp.add_parser(
            'list',
            help='List all Flows.',
            formatter_class=_chf,
        )
    )

    set_status_parser(
        sp.add_parser(
            'status',
            help='Get the status of a Flow.',
            formatter_class=_chf,
        )
    )

    set_remove_parser(
        sp.add_parser(
            'remove',
            help='Remove Flow(s).',
            formatter_class=_chf,
        )
    )

    set_new_project_parser(
        sp.add_parser(
            'new',
            help='Create a new project.',
            description='Create a new Jina project via template.',
            formatter_class=_chf,
        )
    )

    set_update_parser(
        sp.add_parser(
            'update',
            help='Update a Flow',
            formatter_class=_chf,
        )
    )

    set_restart_parser(
        sp.add_parser(
            'restart',
            help='Restart a Flow, executor or gateway',
            formatter_class=_chf,
        )
    )

    set_pause_parser(
        sp.add_parser(
            'pause',
            help='Pause a Flow',
            formatter_class=_chf,
        )
    )

    set_resume_parser(
        sp.add_parser(
            'resume',
            help='Resume a paused Flow',
            formatter_class=_chf,
        )
    )

    set_scale_parser(
        sp.add_parser('scale', help='Scale executor of Flow', formatter_class=_chf)
    )

    sp.add_parser(
        'survey',
        help='Tell us your experience and help us improve.',
        formatter_class=_chf,
    )

    return parser
