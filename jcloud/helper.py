import asyncio
import json
import logging
import os
import re
import shutil
import string
import sys
import tempfile
import threading
import warnings
from contextlib import contextmanager
from distutils.version import LooseVersion
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Union, Dict, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import pkg_resources
import yaml
from rich import print
from rich.highlighter import ReprHighlighter
from rich.panel import Panel

__windows__ = sys.platform == 'win32'


def _version_check(package: str = None, github_repo: str = None):
    try:

        if not package:
            package = vars(sys.modules[__name__])['__package__']
        if not github_repo:
            github_repo = package

        cur_ver = LooseVersion(pkg_resources.get_distribution(package).version)
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
                sorted(LooseVersion(v) for v in releases.keys() if '.dev' not in v)
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


def get_logger():
    from rich.logging import RichHandler

    logging.basicConfig(
        level=os.environ.get('JCLOUD_LOGLEVEL', 'DEBUG'),
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


def valid_uri(uses):
    try:
        return urlparse(uses).scheme in (
            'docker',
            'jinahub+docker',
            'jinahub+sandbox',
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


# Code below was ported over from JAML class in jina; we need to utiltiy of expand_dict during the normalization process.

context_regex_str = r'\${{\s[a-zA-Z0-9_]*\s}}'
context_var_regex = re.compile(
    context_regex_str
)  # matches expressions of form '${{ var }}'

context_dot_regex_str = (
    r'\${{\sCONTEXT\.[a-zA-Z0-9_]*\s}}|\${{\scontext\.[a-zA-Z0-9_]*\s}}'
)
context_dot_regex = re.compile(
    context_dot_regex_str
)  # matches expressions of form '${{ ENV.var }}' or '${{ env.var }}'

new_env_regex_str = r'\${{\sENV\.[a-zA-Z0-9_]*\s}}|\${{\senv\.[a-zA-Z0-9_]*\s}}'
new_env_var_regex = re.compile(
    new_env_regex_str
)  # matches expressions of form '${{ ENV.var }}' or '${{ env.var }}'

env_var_deprecated_regex_str = r'\$[a-zA-Z0-9_]*'
env_var_deprecated_regex = re.compile(
    r'\$[a-zA-Z0-9_]*'
)  # matches expressions of form '$var'

env_var_regex_str = env_var_deprecated_regex_str + '|' + new_env_regex_str
env_var_regex = re.compile(env_var_regex_str)  # matches either of the above

yaml_ref_regex = re.compile(
    r'\${{([\w\[\].]+)}}'
)  # matches expressions of form '${{root.name[0].var}}'


class ContextVarTemplate(string.Template):
    delimiter = '$$'  # variables that should be substituted with values from the context are internally denoted with '$$'


def expand_dict(
    d: Dict,
    context: Optional[Union[Dict, SimpleNamespace]] = None,
    resolve_cycle_ref=True,
    resolve_passes: int = 3,
) -> Dict[str, Any]:
    """
    Expand variables from YAML file.
    :param d: yaml file loaded as python dict
    :param context: context replacement variables in a dict, the value of the dict is the replacement.
    :param resolve_cycle_ref: resolve internal reference if True.
    :param resolve_passes: number of rounds to resolve internal reference.
    :return: expanded dict.
    """

    from jina.helper import parse_arg

    expand_map = SimpleNamespace()
    env_map = SimpleNamespace()

    def _scan(sub_d, p):
        if isinstance(sub_d, dict):
            for k, v in sub_d.items():
                if isinstance(v, dict):
                    p.__dict__[k] = SimpleNamespace()
                    _scan(v, p.__dict__[k])
                elif isinstance(v, list):
                    p.__dict__[k] = list()
                    _scan(v, p.__dict__[k])
                else:
                    p.__dict__[k] = v
        elif isinstance(sub_d, list):
            for idx, v in enumerate(sub_d):
                if isinstance(v, dict):
                    p.append(SimpleNamespace())
                    _scan(v, p[idx])
                elif isinstance(v, list):
                    p.append(list())
                    _scan(v, p[idx])
                else:
                    p.append(v)

    def _replace(sub_d, p, resolve_ref=False):

        if isinstance(sub_d, dict):
            for k, v in sub_d.items():
                if isinstance(v, (dict, list)):
                    _replace(v, p.__dict__[k], resolve_ref)
                else:
                    if isinstance(v, str):
                        if resolve_ref and yaml_ref_regex.findall(v):
                            sub_d[k] = _resolve_yaml_reference(v, p)
                        else:
                            sub_d[k] = _sub(v)
        elif isinstance(sub_d, list):
            for idx, v in enumerate(sub_d):
                if isinstance(v, (dict, list)):
                    _replace(v, p[idx], resolve_ref)
                else:
                    if isinstance(v, str):
                        if resolve_ref and yaml_ref_regex.findall(v):
                            sub_d[idx] = _resolve_yaml_reference(v, p)
                        else:
                            sub_d[idx] = _sub(v)

    def _var_to_substitutable(v, exp=context_var_regex):
        def repl_fn(matchobj):
            return '$$' + matchobj.group(0)[4:-3]

        return re.sub(exp, repl_fn, v)

    def _to_env_var_synatx(v):
        v = _var_to_substitutable(v, new_env_var_regex)

        def repl_fn(matchobj):
            match_str = matchobj.group(0)
            match_str = match_str.replace('ENV.', '')
            match_str = match_str.replace('env.', '')
            return match_str[1:]

        return re.sub(r'\$\$[a-zA-Z0-9_.]*', repl_fn, v)

    def _to_normal_context_var(v):
        def repl_fn(matchobj):
            match_str = matchobj.group(0)
            match_str = match_str.replace('CONTEXT.', '')
            match_str = match_str.replace('context.', '')
            return match_str

        return re.sub(context_dot_regex, repl_fn, v)

    def _sub(v):

        # substitute template with actual value either from context or env variable
        # v could contain template of the form
        #
        # 1)    ${{ var }},${{ context.var }},${{ CONTEXT.var }} when need to be parsed with the context dict
        # or
        # 2 )   ${{ ENV.var }},${{ env.var }},$var ( deprecated) when need to be parsed with env
        #
        #
        # internally env var (1) and context var (2) are treated differently, both of them are cast to a unique and
        # normalize template format and then are parsed
        # 1) context variables placeholder are cast to $$var then we use the ContextVarTemplate to parse the context
        # variables
        # 2) env variables placeholder are cast to $var then we leverage the os.path.expandvars to replace by
        # environment variables.

        if env_var_deprecated_regex.findall(v) and not env_var_regex.findall(
            v
        ):  # catch expressions of form '$var'
            warnings.warn(
                'Specifying environment variables via the syntax `$var` is deprecated.'
                'Use `${{ ENV.var }}` instead.',
                category=DeprecationWarning,
            )
        if new_env_var_regex.findall(v):  # handle expressions of form '${{ ENV.var}}',
            v = _to_env_var_synatx(v)
        if context_dot_regex.findall(v):
            v = _to_normal_context_var(v)
        if context_var_regex.findall(v):  # handle expressions of form '${{ var }}'
            v = _var_to_substitutable(v)
            if context:
                v = ContextVarTemplate(v).safe_substitute(
                    context
                )  # use vars provided in context
        v = os.path.expandvars(
            v
        )  # gets env var and parses to python objects if neededd
        return parse_arg(v)

    def _resolve_yaml_reference(v, p):

        org_v = v
        # internal references are of the form ${{path}} where path is a yaml path like root.executors[0].name

        def repl_fn(matchobj):
            match_str = matchobj.group(0)
            match_str_origin = match_str

            match_str = re.sub(
                yaml_ref_regex, '{\\1}', match_str
            )  # from ${{var}} to {var} to leverage python formatter

            try:
                # "root" context is now the global namespace
                # "this" context is now the current node namespace
                match_str = match_str.format(root=expand_map, this=p, ENV=env_map)
            except AttributeError as ex:
                raise AttributeError(
                    'variable replacement is failed, please check your YAML file.'
                ) from ex
            except KeyError:
                return match_str_origin

            return match_str

        v = re.sub(yaml_ref_regex, repl_fn, v)

        return parse_arg(v)

    _scan(d, expand_map)
    _scan(dict(os.environ), env_map)

    # first do var replacement
    _replace(d, expand_map)

    # do `resolve_passes` rounds of scan-replace to resolve internal references
    for _ in range(resolve_passes):
        # rebuild expand_map
        expand_map = SimpleNamespace()
        _scan(d, expand_map)

        # resolve internal reference
        if resolve_cycle_ref:
            _replace(d, expand_map, resolve_ref=True)

    return d


class EnvironmentVariables:
    def __init__(self, envs: Dict):
        self._env_keys_added: Dict = envs

    def __enter__(self):
        for key, val in self._env_keys_added.items():
            os.environ[key] = str(val)

    def __exit__(self, *args, **kwargs):
        for key in self._env_keys_added.keys():
            os.unsetenv(key)
