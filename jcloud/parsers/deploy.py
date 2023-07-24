from .helper import _chf


def set_deploy_parser(subparser):

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
