import asyncio
import json
import logging
import os
import shutil
import sys
import tempfile
import threading
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Union
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import pkg_resources
import yaml
from packaging.version import Version
from rich import print
from rich.highlighter import ReprHighlighter
from rich.panel import Panel

from .env_helper import EnvironmentVariables, expand_dict

__windows__ = sys.platform == 'win32'


def _version_check(package: str = None, github_repo: str = None):
    try:

        if not package:
            package = vars(sys.modules[__name__])['__package__']
        if not github_repo:
            github_repo = package

        cur_ver = Version(pkg_resources.get_distribution(package).version)
        req = Request(
            f'https://pypi.python.org/pypi/{package}/json',
            headers={'User-Agent': 'Mozilla/5.0'},
        )
        with urlopen(
            req, timeout=1
        ) as resp:  # 'with' is important to close the resource after use
            j = json.load(resp)
            releases = j.get('releases', {})
            latest_release_ver = list(
                sorted(Version(v) for v in releases.keys() if '.dev' not in v)
            )[-1]
            if cur_ver < latest_release_ver:
                print(
                    Panel(
                        f'You are using [b]{package} {cur_ver}[/b], but [bold green]{latest_release_ver}[/] is available. '
                        f'You may upgrade it via [b]pip install -U {package}[/b]. [link=https://github.com/jina-ai/{github_repo}/releases]Read Changelog here[/link].',
                        title=':new: New version available!',
                        width=50,
                    )
                )
    except Exception:
        # no network, too slow, PyPi is down
        pass


def is_latest_version(package: str = None, github_repo: str = None) -> None:
    """Check if there is a latest version from Pypi, set env `NO_VERSION_CHECK` to disable it.

    :param package: package name if none auto-detected
    :param github_repo: repo name that contains CHANGELOG if none then the same as package name
    """

    threading.Thread(target=_version_check, args=(package, github_repo)).start()


def get_logger(name='jcloud'):
    from rich.logging import RichHandler

    logger = logging.getLogger(name)
    logger.setLevel(os.environ.get('JCLOUD_LOGLEVEL', 'INFO'))

    if logger.hasHandlers():
        logger.handlers.clear()
    rich_handler = RichHandler(rich_tracebacks=True)
    formatter = logging.Formatter('%(message)s')
    rich_handler.setFormatter(formatter)
    logger.addHandler(rich_handler)

    return logger


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


def valid_uri(uses):
    try:
        return urlparse(uses).scheme in (
            'docker',
            'jinahub+docker',
            'jinahub+sandbox',
            'jinahub+serverless',
            'jinahub',
        )
    except Exception:
        return False


def normalized(path: Union[str, Path], envs: Dict):
    _normalized = True
    with open(path) as f:
        _flow_dict = yaml.safe_load(f.read())

    if 'executors' in _flow_dict:
        with EnvironmentVariables(envs):
            expand_dict(_flow_dict, context=envs)
        for executor in _flow_dict['executors']:
            uses = executor.get('uses', None)
            if uses is None:
                continue
            elif valid_uri(uses):
                continue
            else:
                _normalized = False
    return _normalized


class CustomHighlighter(ReprHighlighter):
    highlights = ReprHighlighter.highlights + [
        r"(?P<url>(grpc|grpcs)://[-0-9a-zA-Z$_+!`(),.?/;:&=%#]*)"
    ]


def remove_prefix(s: str, prefix: str):
    return s[len(prefix) :] if s.startswith(prefix) else s


def prepare_flow_model_for_render(response: Dict) -> None:
    # 'gateway' and 'endpoints' should be mutually exclusive.
    if response['gateway']:
        del response['endpoints']
    elif response['endpoints']:
        del response['gateway']

    if response['dashboards']:
        # Extra handle for 'dashboards' key; the value is a map
        # but since we only have monitoring dashboard at the moment,
        # for simplicity we turn the map to a string for display purpose.
        response['dashboards'] = response['dashboards']['monitoring']
    else:
        del response['dashboards']
