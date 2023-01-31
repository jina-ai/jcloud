import os
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, Union
from hubble.executor.helper import parse_hub_uri

import requests
from dotenv import dotenv_values

from .constants import CONSTANTS
from .helper import get_logger

GPU_DOCKERFILE = 'Dockerfile.gpu'

logger = get_logger()


@dataclass
class ExecutorData:
    """Basic Executor Data Class"""

    name: str = None
    id: str = None
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
    if executor.id is not None:
        _hubble_uses = f'jinahub+docker://{executor.id}'
    else:
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

    executor_id = HubIO(args).push().get('id')
    executor.id = executor_id
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
    return load_envs(workspace / CONSTANTS.DEFAULT_ENV_FILENAME)


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
            _, name, tag, secret = parse_hub_uri(uses)
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


def push_executors_to_hubble(
    executors: List[ExecutorData],
    tag: Optional[str] = "latest",
    secret: Optional[str] = "",
    verbose: Optional[bool] = False,
):
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


def normalize_flow(flow_data: Dict, executors: List['ExecutorData']) -> Dict[str, Any]:

    for i, (exec_dict, exec_data) in enumerate(zip(flow_data['executors'], executors)):
        if exec_data.hubble_url is None:
            hubble_url = get_hubble_uses(exec_data)
            flow_data['executors'][i]['uses'] = hubble_url
        else:
            scheme, _, _, _ = parse_hub_uri(flow_data['executors'][i]['uses'])
            if scheme == 'jinahub':
                flow_data['executors'][i]['uses'] = exec_data.hubble_url
        if 'install_requirements' in exec_dict:
            flow_data['executors'][i].pop('install_requirements')

    return flow_data


def flow_normalize(
    path: Path,
    tag: Optional[str] = "latest",
    secret: Optional[str] = "",
    verbose: Optional[bool] = False,
    output_path: Optional[Path] = None,
) -> str:
    from jina.jaml import JAML

    if isinstance(path, str):
        path = Path(path)

    flow_file_in_path = path.is_file()

    if path.is_file():
        flow_file = path.name
        path = path.parent

    envs = get_filename_envs(path)
    flow_dict = load_flow_data(
        path / flow_file
        if flow_file_in_path
        else path / CONSTANTS.DEFAULT_FLOW_FILENAME,
        envs=envs,
    )

    if not 'executors' in flow_dict:
        logger.warning('`executors` not found in Flow yaml. Nothing to normalize...')
        return

    executors = inspect_executors(
        flow_dict,
        workspace=path,
        tag=tag,
        secret=secret,
    )

    push_executors_to_hubble(executors, tag, secret, verbose)

    normed_flow = normalize_flow(flow_dict.copy(), executors)
    normed_flow_path = CONSTANTS.NORMED_FLOWS_DIR / path.name

    # override the normed_flow_path
    output_flow_file = flow_file
    if output_path is not None:
        if isinstance(output_path, str):
            output_path = Path(output_path)
        if output_path.suffix.lower() in ('.yml', '.yaml'):
            output_flow_file = output_path.name
            output_path = output_path.parent
        normed_flow_path = output_path

    if not normed_flow_path.exists():
        os.makedirs(normed_flow_path)

    if output_path is not None:
        cm = open(normed_flow_path / output_flow_file, 'w')
    else:
        cm = tempfile.NamedTemporaryFile(
            'w',
            prefix=f'{flow_file.strip(".yml") if flow_file_in_path else CONSTANTS.DEFAULT_FLOW_FILENAME.strip(".yml")}-',
            suffix='.yml',
            dir=normed_flow_path,
            delete=False,
        )
    with cm as f:
        JAML.dump(normed_flow, stream=f)

    logger.info(f'Flow is normalized: \n\n{normed_flow}')
    logger.info(f'Flow written to: {f.name}')
    return f.name
