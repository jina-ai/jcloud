import asyncio
import logging
import os
import shutil
import sys
import tempfile
import warnings
from contextlib import contextmanager
from pathlib import Path
import json

__windows__ = sys.platform == 'win32'


def _version_check(package: str = None):

    try:
        import warnings
        from urllib.request import Request, urlopen
        import pkg_resources
        from rich import print
        from rich.panel import Panel
        from distutils.version import LooseVersion

        if not package:
            package = vars(sys.modules[__name__])['__package__']

        cur_ver = LooseVersion(pkg_resources.get_distribution(package).version)
        req = Request(
            f'https://pypi.python.org/pypi/{package}/json',
            headers={'User-Agent': 'Mozilla/5.0'},
        )
        with urlopen(
            req, timeout=5
        ) as resp:  # 'with' is important to close the resource after use
            j = json.load(resp)
            releases = j.get('releases', {})
            latest_release_ver = list(
                sorted(LooseVersion(v) for v in releases.keys() if '.dev' not in v)
            )[-1]
            if cur_ver < latest_release_ver:
                print(
                    Panel(
                        f'You are using [b]{package} {cur_ver}[/b], but [bold green]{latest_release_ver}[/] is available. '
                        f'You may upgrade it via [b]pip install -U {package}[/b]. [link=https://github.com/jina-ai/{package}/blob/main/CHANGELOG.md]Read Changelog here[/link].',
                        title=':new: New version available!',
                        width=50,
                    )
                )
    except Exception as ex:
        # no network, too slow, PyPi is down
        get_logger().debug(ex)


def is_latest_version(package: str = None) -> None:
    """Check if there is a latest version from Pypi, set env `NO_VERSION_CHECK` to disable it.

    :param package: package name if none auto detect
    """
    if 'NO_VERSION_CHECK' not in os.environ:
        import threading

        threading.Thread(target=_version_check, daemon=True, args=(package,)).start()


def get_logger():
    from rich.logging import RichHandler

    logging.basicConfig(
        level=os.environ.get('JCLOUD_LOGLEVEL'),
        format='%(message)s',
        datefmt='[%X]',
        handlers=[RichHandler(rich_tracebacks=True)],
    )

    return logging.getLogger('jcloud')


def get_or_reuse_loop():
    """
    Get a new eventloop or reuse the current opened eventloop.

    :return: A new eventloop or reuse the current opened eventloop.
    """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_closed():
            raise RuntimeError
    except RuntimeError:
        _update_policy()
        # no running event loop
        # create a new loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def _update_policy():
    if __windows__:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    elif 'JINA_DISABLE_UVLOOP' in os.environ:
        return
    else:
        try:
            import uvloop

            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        except ModuleNotFoundError:
            warnings.warn(
                'Install `uvloop` via `pip install uvloop` for better performance.'
            )


def get_pbar(description, disable=False, total=4):
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
    )

    pbar = Progress(
        SpinnerColumn(),
        TextColumn('[bold]{task.fields[title]}'),
        '•',
        TextColumn('[dim]{task.description}...'),
        BarColumn(bar_width=20),
        MofNCompleteColumn(),
        '•',
        TimeElapsedColumn(),
        transient=True,
        disable=disable,
    )

    pb_task = pbar.add_task(description, total=total, start=False, title='')
    return pbar, pb_task


@contextmanager
def zipdir(directory: Path) -> Path:
    _zip_dest = tempfile.mkdtemp()
    _zip_name = shutil.make_archive(
        base_name=directory.name,
        format='zip',
        root_dir=str(directory),
    )
    shutil.move(_zip_name, _zip_dest)
    yield Path(os.path.join(_zip_dest, os.path.basename(_zip_name)))
    shutil.rmtree(_zip_dest)
