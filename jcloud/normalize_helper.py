import os
import uuid
import requests
import tempfile
import time

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dotenv import dotenv_values
from concurrent.futures import ThreadPoolExecutor, as_completed
from textwrap import dedent
from http import HTTPStatus

from .helper import get_logger
from .constants import CONSTANTS

GPU_DOCKERFILE = 'Dockerfile.gpu'

logger = get_logger()


@dataclass
class ExecutorData:
    """Basic Executor Data Class"""

    name: str = None
    src_dir: Optional[Union[str, Path]] = None
    tag: Optional[str] = None
    yaml_dict: Optional[Dict] = None
    secret: Optional[str] = None
    device: Optional[str] = None
    hubble_url: Optional[str] = None
    hubble_exists: bool = False


class FlowYamlNotFound(FileNotFoundError):
    pass


def get_hubble_uses(executor: 'ExecutorData') -> str:
    _hubble_uses = f'jinahub+docker://{executor.name}'

    if executor.secret:
        _hubble_uses += f':{executor.secret}'
    if executor.tag:
        _hubble_uses += f'/{executor.tag}'
    return _hubble_uses


def generate_manifest(executor: 'ExecutorData', id: str):
    return dedent(
        f"""\
        # This file is automatically generated by Wolf normalizer plugin.
        # It is not intended for manual editing.

        manifest_version: 1
        name: {executor.name}
        description: An executor automatically uploaded by Wolf.
        keywords: [wolf-executor, private, {id}]
        """
    )


def hubble_exists(executor: 'ExecutorData', secret: Optional[str] = None) -> bool:
    return (
        requests.get(
            url='https://api.hubble.jina.ai/v2/executor/getMeta',
            params={'id': executor.name, 'secret': secret},
        ).status_code
        == HTTPStatus.OK
    )


def hubble_push(
    executor: 'ExecutorData',
    id: Optional[str] = None,
    tag: Optional[str] = 'latest',
    secret: Optional[str] = None,
    verbose: Optional[bool] = False,
):
    from hubble.executor.hubio import HubIO
    from hubble.executor.parsers import set_hub_push_parser

    args_list = [
        str(executor.src_dir),
        '--tag',
        tag,
        '--secret',
        secret,
        '--public',
        '--no-usage',
    ]
    if verbose:
        args_list.append('--verbose')

    args = set_hub_push_parser().parse_args(args_list)

    manifest_file = Path(executor.src_dir / 'manifest.yml')

    if id is not None:
        # append the `id` as the suffix to executor name
        executor.name = f'{executor.name}-{id}'

    # automatically generate manifest YAML always, even if exists.
    content = generate_manifest(executor, id)
    with open(manifest_file, 'w') as f:
        f.write(content)

    if hubble_exists(executor, secret):
        args.force_update = executor.name

    HubIO(args).push()

    return executor


def load_envs(envfile: Union[str, Path]) -> Dict:
    if isinstance(envfile, str):
        envfile = Path(envfile)
    
    if envfile.exists():
        return dotenv_values(envfile)
    else:
        logger.info(f'envfile {envfile.name} not found.')
        return {}


def validate_flow_yaml_exists(path: Path):
    if not Path(path).exists():
        raise FlowYamlNotFound(path.name)


def get_filename_envs(workspace: Path) -> Dict:
    return CONSTANTS.DEFAULT_FLOW_FILENAME, load_envs(
        workspace / CONSTANTS.DEFAULT_ENV_FILENAME
    )


def load_flow_data(path: Union[str, Path], envs: Optional[Dict] = None) -> Dict:
    from jina.jaml import JAML

    if isinstance(path, str):
        path = Path(path)

    logger.info(f'Loading Flow YAML {path.name} ...')
    with open(path) as f:
        flow_dict = JAML.load(f, substitute=True, context=envs)
        if 'jtype' not in flow_dict or flow_dict['jtype'] != 'Flow':
            raise ValueError(f'The file `{path}` is not a valid Flow YAML')
        return flow_dict


def inspect_executors(
    flow_dict: Dict,
    workspace: Path,
    tag: Optional[str] = None,
    secret: Optional[str] = None,
) -> List[ExecutorData]:
    from hubble.executor.helper import parse_hub_uri
    from jina import __version__
    from jina.jaml import JAML

    executors = []
    for i, executor in enumerate(flow_dict['executors']):
        executor_name = executor.get('name', f'executor{i}')
        try:
            uses = executor['uses']

            uses_with = executor.get('uses_with', {})

            # TODO: check if gpu tag even exists (not for now, create a follow up ticket)
            device = uses_with.get('device', None)

            if not isinstance(uses, str):
                raise ValueError
            scheme, name, tag, secret = parse_hub_uri(uses)
            data = ExecutorData(
                name=name,
                tag=tag,
                secret=secret,
                device=device,
                hubble_exists=True,
            )
            data.hubble_url = get_hubble_uses(data)

        except KeyError:
            data = ExecutorData(
                name=executor_name,
                hubble_url=f'jinaai/jina:{__version__}-py38-standard',
            )
        except ValueError:
            if isinstance(uses, str) and uses.endswith(('.yml', '.yaml')):
                uses_path = workspace / uses

                with open(uses_path) as f:
                    yaml_dict = JAML.load(f, substitute=True, context={})

                cls_name = yaml_dict.get('jtype', '')
                src_dir = uses_path.parent
                data = ExecutorData(
                    name=f'{executor_name}-{cls_name}',
                    src_dir=src_dir,
                    device=device,
                    yaml_dict=yaml_dict,
                    hubble_exists=False,
                    tag=tag,
                    secret=secret,
                )
            else:
                cls_name = uses.get('jtype', '')
                py_modules = uses['metas'].get('py_modules', [''])
                src_dir = Path(workspace, py_modules[0]).parent
                data = ExecutorData(
                    name=f'{executor_name}-{cls_name}',
                    src_dir=src_dir,
                    device=device,
                    yaml_dict=executor,
                    hubble_exists=False,
                    tag=tag,
                    secret=secret,
                )

        executors.append(data)

    return executors


def normalize_flow(flow_data: Dict, executors: List['ExecutorData']) -> Dict[str, Any]:
    from jina.jaml import JAML

    for i, (exec_dict, exec_data) in enumerate(zip(flow_data['executors'], executors)):
        if exec_data.hubble_url is None:
            hubble_url = get_hubble_uses(exec_data)
            flow_data['executors'][i]['uses'] = hubble_url

        if 'install_requirements' in exec_dict:
            flow_data['executors'][i].pop('install_requirements')

    return flow_data


def flow_normalize(
    path: Path,
    tag: Optional[str] = "latest",
    secret: Optional[str] = "",
    verbose: Optional[bool] = False,
) -> str:
    from jina.jaml import JAML

    if isinstance(path, str):
        path = Path(path)

    if path.is_file():
        path = path.parent

    flow_file, envs = get_filename_envs(path)
    flow_dict = load_flow_data(path / flow_file, envs=envs)

    if not 'executors' in flow_dict:
        logger.warning('`executors` not found in Flow yaml. Nothing to normalize...')
        return

    executors = inspect_executors(
        flow_dict,
        workspace=path,
        tag=tag,
        secret=secret,
    )

    _executors_to_push = []
    for executor in executors:
        if executor.hubble_url:
            logger.debug(f'Skipping {executor.name} with {executor.hubble_url} ...')
            continue
        _executors_to_push.append(executor)

    id = uuid.uuid4().hex[:10]
    with ThreadPoolExecutor() as tpe:
        for _e_list in [
            _executors_to_push[pos : pos + 3]
            for pos in range(0, len(_executors_to_push), 3)
        ]:
            logger.info(
                'Pushing following Executors to hubble '
                f'{", ".join(map(lambda _e: str(_e.src_dir), _e_list))}...'
            )
            _futures = [
                tpe.submit(hubble_push, _e, id, tag, secret, verbose) for _e in _e_list
            ]
            for _fut in as_completed(_futures):
                _ = _fut.result()

    normed_flow = normalize_flow(flow_dict.copy(), executors)
    normed_flow_path = CONSTANTS.NORMED_FLOWS_DIR / path.name
    if not normed_flow_path.exists():
        os.makedirs(normed_flow_path)
    with tempfile.NamedTemporaryFile(
        'w',
        prefix=f'flow-{id}-',
        suffix='.yml',
        dir=normed_flow_path,
        delete=False,
    ) as f:
        JAML.dump(normed_flow, stream=f)
    
    logger.info(f'Flow is normalized: \n\n{normed_flow}')
    logger.info(f'Flow written to: {f.name}')
    return f.name
