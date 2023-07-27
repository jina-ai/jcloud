from typing import List
from argparse import ArgumentParser

from .helper import _chf
from ..constants import Resources


def get_main_parser(parser=None):
    """The main parser for Jina

    :return: the parser
    """
    from .base import set_base_parser, set_new_project_parser
    from .deploy import set_deploy_parser
    from .list import set_list_resource_parser
    from .get import set_get_resource_parser
    from .create import set_create_resource_parser
    from .remove import set_remove_resource_parser
    from .status import set_status_parser
    from .normalize import set_normalize_parser
    from .update import set_update_resource_parser
    from .logs import set_logs_resource_parser
    from .custom_actions import (
        set_restart_parser,
        set_pause_parser,
        set_resume_parser,
        set_scale_parser,
        set_recreate_parser,
    )

    # create the top-level parser
    parser = set_base_parser(parser=parser)

    sp = parser.add_subparsers(
        dest='jc_cli',
        required=True,
    )

    sp.add_parser(
        'login',
        help='Login to Jina AI Cloud / Ecosystem.',
        formatter_class=_chf,
    )

    sp.add_parser(
        'logout',
        help='Logout from Jina AI Cloud / Ecosystem.',
        formatter_class=_chf,
    )

    resource_parsers = _add_resource_parsers(sp)

    for resource_parser in resource_parsers:
        subparser = resource_parser.add_subparsers(
            dest='subcommand',
            required=True,
        )
        set_list_resource_parser(subparser, resource_parser.prog)
        set_remove_resource_parser(subparser, resource_parser.prog)
        if Resources.Job not in resource_parser.prog:
            set_update_resource_parser(subparser, resource_parser.prog)
        if Resources.Flow in resource_parser.prog:
            set_restart_parser(subparser)
            set_pause_parser(subparser)
            set_resume_parser(subparser)
            set_scale_parser(subparser)
            set_recreate_parser(subparser)
            set_status_parser(subparser)
            set_deploy_parser(subparser)
            set_normalize_parser(subparser)
        if (
            Resources.Flow in resource_parser.prog
            or Resources.Job in resource_parser.prog
        ):
            set_logs_resource_parser(subparser, resource_parser.prog)
        if (
            Resources.Job in resource_parser.prog
            or Resources.Secret in resource_parser.prog
        ):
            resource = (
                Resources.Job
                if Resources.Job in resource_parser.prog
                else Resources.Secret
            )
            set_create_resource_parser(subparser, resource)
            set_get_resource_parser(subparser, resource)

    set_new_project_parser(
        sp.add_parser(
            'new',
            help='Create a new project.',
            description='Create a new Jina project via template.',
            formatter_class=_chf,
        )
    )

    return parser


def _add_resource_parsers(subparser) -> List[ArgumentParser]:
    flow_parser = subparser.add_parser(
        'flow',
        help='Manage Flow(s).',
        formatter_class=_chf,
        aliases=['flows'],
    )

    job_parser = subparser.add_parser(
        'job',
        help='Manage Job(s).',
        formatter_class=_chf,
        aliases=['jobs'],
    )

    secret_parser = subparser.add_parser(
        'secret',
        help='Manage Secret(s).',
        formatter_class=_chf,
        aliases=['secrets'],
    )

    return [flow_parser, job_parser, secret_parser]
