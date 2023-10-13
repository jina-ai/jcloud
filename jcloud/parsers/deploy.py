from .helper import _chf
from ..constants import Resources


def set_deploy_parser(subparser, parser_prog):
    if Resources.Flow in parser_prog:
        set_flow_deploy_parser(subparser)
    elif Resources.Deployment in parser_prog:
        set_deployment_deploy_parser(subparser)


def set_flow_deploy_parser(subparser):
    deploy_parser = subparser.add_parser(
        'deploy',
        help='Deploy a Flow.',
        formatter_class=_chf,
    )

    deploy_parser.add_argument(
        'path',
        type=str,
        help='The local path to a Jina flow project.',
    )


def set_deployment_deploy_parser(subparser):
    deploy_parser = subparser.add_parser(
        'deploy',
        help='Deploy a Deployment.',
        formatter_class=_chf,
    )

    deploy_parser.add_argument(
        'path',
        type=str,
        help='The local path to a Jina deployment project.',
    )
