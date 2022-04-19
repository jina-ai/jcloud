__version__ = '0.0.14'


def _is_latest_version(package):
    try:
        import warnings
        from urllib.request import Request, urlopen

        import pkg_resources

        cur_ver = Version(pkg_resources.get_distribution(package).version)

        req = Request(
            f'https://pypi.python.org/pypi/{package}/json',
            headers={'User-Agent': 'Mozilla/5.0'},
        )
        with urlopen(
            req, timeout=5
        ) as resp:  # 'with' is important to close the resource after use
            latest_release_ver = _parse_latest_release_version(resp)
            if cur_ver < latest_release_ver:
                from rich import print

                print(
                    f'You are using [b]{package} {cur_ver}[/b]. A new version [green][b]{latest_release_ver}[/b][/green] is available. '
                    f'Consider upgrading via [b]pip install -U {package}[/b].'
                )
    except:
        # no network, too slow, PyPi is down
        pass


def main():
    from .parsers import get_main_parser
    import os

    args = get_main_parser().parse_args()

    if args.loglevel:
        os.environ['JCLOUD_LOGLEVEL'] = args.loglevel

    try:
        import threading

        threading.Thread(
            target=_is_latest_version, daemon=True, args=('jcloud',)
        ).start()
        from jcloud import api

        getattr(api, args.cli.replace('-', '_'))(args)
    except KeyboardInterrupt:
        pass
