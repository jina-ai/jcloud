import asyncio
import json
import logging
import os
import sys
import threading
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from dotenv import dotenv_values

from .constants import CONSTANTS

import aiohttp
import pkg_resources
import yaml
from dateutil import tz
from hubble.executor.helper import is_valid_docker_uri, is_valid_sandbox_uri
from packaging.version import Version
from rich import print
from rich.align import Align
from rich.highlighter import ReprHighlighter
from rich.table import Table
from rich.panel import Panel

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
    rich_handler = RichHandler(rich_tracebacks=True, markup=True)
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


def is_valid_serverless_uri(uses):
    """Check to see if the 'uses' is a valid serverless URI.

    Serverless notation is JCloud specific, which we need to handle in addition to
    what Hubble already provides for URI validation.
    """
    try:
        return urlparse(uses).scheme in (
            'jinahub+serverless',
            'jinaai+serverless',
        )
    except Exception:
        return False


def normalized(path: Union[str, Path]):
    _normalized = True

    if isinstance(path, str):
        path = Path(path)
    with open(path) as f:
        _flow_dict = yaml.safe_load(f.read())

    if 'executors' in _flow_dict:
        for executor in _flow_dict['executors']:
            uses = executor.get('uses', None)
            if uses is None:
                continue
            elif (
                is_valid_docker_uri(uses)
                or is_valid_sandbox_uri(uses)
                or is_valid_serverless_uri(uses)
            ):
                continue
            else:
                _normalized = False
    return _normalized


def exit_error(text: str, color: Optional[str] = 'red'):
    print(f'[{color}]{text}[/{color}]')
    exit(1)


class CustomHighlighter(ReprHighlighter):
    highlights = ReprHighlighter.highlights + [
        r"(?P<url>(grpc|grpcs)://[-0-9a-zA-Z$_+!`(),.?/;:&=%#]*)"
    ]


def add_table_row_fn(table: Table, key: str, value: str):
    return lambda: table.add_row(Align(f'[bold]{key}', vertical='middle'), value)


def center_align(value: str):
    return Align(f'[bold]{value}[/bold]', align='center')


def remove_prefix(s: str, prefix: str):
    return s[len(prefix) :] if s.startswith(prefix) else s


def jsonify(data: Union[Dict, List]) -> str:
    return (
        json.dumps(data, indent=2, sort_keys=True)
        if isinstance(data, (dict, list))
        else data
    )


def yamlify(data: Union[Dict, List]) -> str:
    return (
        yaml.dump(data, indent=2, sort_keys=False, default_flow_style=False)
        if isinstance(data, (dict, list))
        else data
    )


def get_endpoints_from_response(response: Dict) -> Dict:
    return response.get('status', {}).get('endpoints', {})


def get_str_endpoints_from_response(response: Dict) -> str:
    return json.dumps(get_endpoints_from_response(response))


def get_grafana_from_response(response: Dict) -> str:
    if response:
        dashboards = response.get('status', {}).get('dashboards', {})
        if dashboards is None:
            return ''
    return dashboards.get('grafana', '')


def get_phase_from_response(response: Dict) -> str:
    return response.get('status', {}).get('phase', '')


def get_cph_from_response(response: Dict) -> str:
    return str(response.get('CPH', {}).get('total', ''))


def cleanup_dt(dt) -> str:
    try:
        return (
            datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f%z')
            .astimezone(tz=tz.tzlocal())
            .strftime('%d-%b-%Y %H:%M GMT %z')
        )
    except ValueError:
        try:
            return (
                datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S%z')
                .astimezone(tz=tz.tzlocal())
                .strftime('%d-%b-%Y %H:%M GMT %z')
            )
        except ValueError:
            return dt
    except Exception as e:
        return dt


def get_dashboard_from_flowid(flow_id: str) -> str:
    ns = flow_id.split('-')[-1]
    return f'https://dashboard.wolf.jina.ai/flow/{ns}'


def jcloud_logs_from_response(flow_id: str, response: Dict) -> str:
    if 'jcloud' not in response:
        return get_dashboard_from_flowid(flow_id)
    else:
        try:
            return response['jcloud']['url']
        except KeyError:
            return get_dashboard_from_flowid(flow_id)


def get_dict_list_key_path(collection, keys):
    col = collection
    for k in keys:
        try:
            col = col[k]
        except (KeyError, IndexError, TypeError) as e:
            return None
    return col


def get_condition_from_status(status):
    try:
        sts = status["status"]
        conds = sts["conditions"]
        for c in conds:
            if c["type"] == "ReadinessSuccessful":
                return c
    except KeyError:
        return None


def get_aiohttp_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False, limit=5, force_close=True),
    )


def load_envs(envfile: Union[str, Path]) -> Dict:
    if isinstance(envfile, str):
        envfile = Path(envfile)

    if envfile.exists():
        return dotenv_values(envfile)
    else:
        get_logger().debug(f'envfile {envfile.name} not found.')
        return {}


class FlowYamlNotFound(FileNotFoundError):
    pass


class JCloudLabelsError(TypeError):
    pass


def stringify(v: Any) -> str:
    if isinstance(v, str):
        return v
    elif isinstance(v, int) or isinstance(v, float):
        return str(v)
    else:
        raise JCloudLabelsError(f'labels can\'t be of type {type(v)}')


def stringify_labels(flow_dict: Dict) -> Dict:
    global_jcloud_labels = flow_dict.get('jcloud', {}).get('labels', None)
    if global_jcloud_labels:
        for k, v in flow_dict['jcloud']['labels'].items():
            flow_dict['jcloud']['labels'][k] = stringify(v)
    gateway_jcloud_labels = (
        flow_dict.get('gateway', {}).get('jcloud', {}).get('labels', None)
    )
    if gateway_jcloud_labels:
        for k, v in flow_dict['gateway']['jcloud']['labels'].items():
            flow_dict['gateway']['jcloud']['labels'][k] = stringify(v)

    executors = flow_dict.get('executors', [])
    for idx in range(len(executors)):
        executor_jcloud_labels = (
            flow_dict['executors'][idx].get('jcloud', {}).get('labels', None)
        )
        if executor_jcloud_labels:
            for k, v in flow_dict['executors'][idx]['jcloud']['labels'].items():
                flow_dict['executors'][idx]['jcloud']['labels'][k] = stringify(v)
    return flow_dict


def validate_flow_yaml_exists(path: Path):
    if not Path(path).exists():
        raise FlowYamlNotFound(path.name)


def get_filename_envs(workspace: Path) -> Dict:
    return load_envs(workspace / CONSTANTS.DEFAULT_ENV_FILENAME)


def load_flow_data(path: Union[str, Path], envs: Optional[Dict] = None) -> Dict:
    from jina.jaml import JAML

    if isinstance(path, str):
        path = Path(path)

    get_logger().debug(f'Loading Flow YAML {path.name} ...')
    with open(path) as f:
        flow_dict = JAML.load(f, substitute=True, context=envs)
        if 'jtype' not in flow_dict or flow_dict['jtype'] != 'Flow':
            raise ValueError(f'The file `{path}` is not a valid Flow YAML')
        flow_dict = check_and_set_jcloud_versions(flow_dict)
        flow_dict = stringify_labels(flow_dict)
        return flow_dict


def update_flow_yml_and_write_to_file(
    flow_path: Path,
    secret_name: str,
    secret_data: Dict,
):
    from jina.jaml import JAML

    validate_flow_yaml_exists(flow_path)
    _flow_dict = load_flow_data(flow_path, get_filename_envs(flow_path.parent))

    flow_with_secret_path = flow_path.parent / f'{flow_path.stem}-{secret_name}.yml'

    secret_yaml = {}
    for secret_key, _ in secret_data.items():
        secret_yaml[secret_key] = {'name': secret_name, 'key': secret_key}
    with_args = _flow_dict.get('with', None)
    if not with_args:
        _flow_dict['with'] = {'env_from_secret': secret_yaml}
    else:
        env_from_secret = with_args.get('env_from_secret', None)
        if not env_from_secret:
            _flow_dict['with']['env_from_secret'] = secret_yaml
        else:
            _flow_dict['with']['env_from_secret'].update(secret_yaml)
    JAML.dump(_flow_dict, stream=open(flow_with_secret_path, 'w'))
    return flow_with_secret_path


def exit_if_flow_defines_secret(flow_path):
    if isinstance(flow_path, str):
        flow_path = Path(flow_path)
    if flow_path.is_dir():
        flow_path = flow_path / 'flow.yml'

    flow_dict = load_flow_data(flow_path)
    env_from_secret = flow_dict.get('with', {}).get('env_from_secret', None)
    if env_from_secret:
        exit_error(
            'A Flow cannot be deployed with Secrets. Follow these steps to add a Secret to your Flow:'
            '\n\t1.Deploy a Flow with no Secrets.'
            '\n\t2.Create a Secret for your flow with `jc create secret <secret-name> -f <flow-id> --from-literal <secret-data> --update`.',
            'cyan',
        )


class JCloudLabelsError(TypeError):
    pass


def stringify(v: Any) -> str:
    if isinstance(v, str):
        return v
    elif isinstance(v, int) or isinstance(v, float):
        return str(v)
    else:
        raise JCloudLabelsError(f'labels can\'t be of type {type(v)}')


def stringify_labels(flow_dict: Dict) -> Dict:
    global_jcloud_labels = flow_dict.get('jcloud', {}).get('labels', None)
    if global_jcloud_labels:
        for k, v in flow_dict['jcloud']['labels'].items():
            flow_dict['jcloud']['labels'][k] = stringify(v)
    gateway_jcloud_labels = (
        flow_dict.get('gateway', {}).get('jcloud', {}).get('labels', None)
    )
    if gateway_jcloud_labels:
        for k, v in flow_dict['gateway']['jcloud']['labels'].items():
            flow_dict['gateway']['jcloud']['labels'][k] = stringify(v)

    executors = flow_dict.get('executors', [])
    for idx in range(len(executors)):
        executor_jcloud_labels = (
            flow_dict['executors'][idx].get('jcloud', {}).get('labels', None)
        )
        if executor_jcloud_labels:
            for k, v in flow_dict['executors'][idx]['jcloud']['labels'].items():
                flow_dict['executors'][idx]['jcloud']['labels'][k] = stringify(v)
    return flow_dict


def check_and_set_jcloud_versions(flow_dict: Dict) -> Dict:
    import docarray
    import jina

    global_jcloud = flow_dict.get('jcloud', None)
    if not global_jcloud:
        flow_dict['jcloud'] = {
            'docarray': docarray.__version__,
            'version': jina.__version__,
        }
        return flow_dict
    docarray_version = global_jcloud.get('docarray', None)
    if not docarray_version:
        flow_dict['jcloud'].update({'docarray': docarray.__version__})
    jina_version = global_jcloud.get('version', None)
    if not jina_version:
        flow_dict['jcloud'].update({'version': jina.__version__})
    return flow_dict
