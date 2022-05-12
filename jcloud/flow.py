import asyncio
import json
import os
from contextlib import suppress
from dataclasses import dataclass
from enum import Enum
from http import HTTPStatus
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from rich import print

from .helper import get_logger, get_or_reuse_loop, get_pbar, normalized, zipdir

WOLF_API = 'https://api.wolf.jina.ai/dev/flows'
LOGSTREAM_API = 'wss://logs.wolf.jina.ai/dev'
ARTIFACT_API = 'https://apihubble.jina.ai/v2/rpc/artifact.upload'

logger = get_logger()

pbar, pb_task = get_pbar(
    '', total=5, disable='JCLOUD_NO_PROGRESSBAR' in os.environ
)  # progress bar for deployment


class Status(str, Enum):
    SUBMITTED = 'SUBMITTED'
    NORMALIZING = 'NORMALIZING'
    NORMALIZED = 'NORMALIZED'
    STARTING = 'STARTING'
    FAILED = 'FAILED'
    ALIVE = 'ALIVE'
    UPDATING = 'UPDATING'
    DELETING = 'DELETING'
    DELETED = 'DELETED'

    @property
    def streamable(self) -> bool:
        return self in (Status.ALIVE, Status.UPDATING, Status.DELETING)

    @property
    def alive(self) -> bool:
        return self == Status.ALIVE

    @property
    def deleted(self) -> bool:
        return self == Status.DELETED


def _exit_if_response_error(response, expected_status):
    if response.status != expected_status:
        if response.status == HTTPStatus.FORBIDDEN:
            _exit_error('[b]WOLF_TOKEN[/b] is not valid. Please check or login again.')
        else:
            _exit_error(
                f'Bad response: expecting [b]{expected_status}[/b], got [b]{response.status}:{response.reason}[/b] from server.'
            )


def _exit_error(text):
    print(f'[red]{text}[/red]')
    exit(1)


@dataclass
class CloudFlow:
    path: Optional[str] = None
    name: Optional[str] = None
    workspace_id: Optional[str] = None
    flow_id: Optional[str] = None
    env_file: Optional[str] = None

    def __post_init__(self):
        from .auth import Auth

        token = Auth.get_auth_token()
        if not token:
            _exit_error(
                'You are not logged in, please login using [b]jcloud login[/b] first.'
            )
        else:
            self.auth_header = {'Authorization': f'token {token}'}

        if self.flow_id and not self.flow_id.startswith('jflow-'):
            # user given id does not starts with `jflow-`
            self.flow_id = f'jflow-{self.flow_id}'
        if self.workspace_id and not self.workspace_id.startswith('jworkspace-'):
            # user given id does not starts with `jflow-`
            self.workspace_id = f'jworkspace-{self.workspace_id}'

    @property
    def host(self) -> str:
        return f'{self.name}-{self.id}.wolf.jina.ai'

    @property
    def id(self) -> str:
        return self.flow_id.split('-')[1]

    @property
    def _loop(self):
        return get_or_reuse_loop()

    @property
    def artifact_metadata(self) -> Dict:
        _path = Path(self.path)
        _tags = {'filename': _path.name if _path.is_file() else 'flow.yml'}
        if self.env_file is not None:
            _env_path = Path(self.env_file)
            if _env_path.exists():
                logger.info(f'Passing env variables from {self.env_file} file')
                _tags.update({'envfile': _env_path.name})
            else:
                _exit_error(f'env file [b]{self.env_file}[/b] not found')
        else:
            _env_path = _path / '.env'
            if _env_path.exists():
                logger.info(f'Passing env variables from default .env file ')
                _tags.update({'envfile': _env_path.name})
        return _tags

    @property
    def envs(self) -> Dict:
        if self.env_file is not None:
            _env_path = Path(self.env_file)
            if _env_path.exists():
                from dotenv import dotenv_values

                return dict(dotenv_values(_env_path))
            else:
                _exit_error(f'env file [b]{self.env_file}[/b] not found')
        else:
            return {}

    async def _zip_and_upload(self, directory: Path) -> str:
        # extra steps for normalizing and normalized
        pbar.update(pb_task, total=7)
        with zipdir(directory=directory) as zipfilepath:
            return await self._upload_project(
                filepaths=[zipfilepath],
                metadata=self.artifact_metadata,
            )

    async def _get_post_params(self):
        params, _post_kwargs = {}, {}
        if self.name:
            params['name'] = self.name
        if self.workspace_id:
            params['workspace'] = self.workspace_id

        _data = aiohttp.FormData()
        _path = Path(self.path)
        if not _path.exists():
            _exit_error(f'Path {self.path} doesn\'t exist.')
        elif _path.is_dir():
            _flow_path = _path / 'flow.yml'
            if _flow_path.exists() and normalized(_flow_path):
                _data.add_field(name='yaml', value=open(_flow_path))
            else:
                params['artifactid'] = await self._zip_and_upload(_path)
        elif _path.is_file():
            if normalized(_path):
                _data.add_field(name='yaml', value=open(_path))
            else:
                # normalize & deploy parent directory
                params['artifactid'] = await self._zip_and_upload(_path.parent)

        if self.envs:
            _data.add_field(name='envs', value=json.dumps(self.envs))

        if _data._fields:
            _post_kwargs['data'] = _data
        _post_kwargs['params'] = params
        return _post_kwargs

    async def _deploy(self):

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=WOLF_API, headers=self.auth_header, **await self._get_post_params()
            ) as response:
                json_response = await response.json()
                _exit_if_response_error(response, HTTPStatus.CREATED)

                if self.name:
                    assert self.name in json_response['name']
                assert Status(json_response['status']) == Status.SUBMITTED

                self.flow_id: str = json_response['id']
                self.workspace_id: str = json_response['workspace']

                logger.debug(
                    f'POST /flows with flow_id {self.flow_id} & request_id {json_response["request_id"]}'
                )

                self._c_logstream_task = asyncio.create_task(
                    CloudFlow.logstream({'request_id': json_response['request_id']})
                )
                return json_response

    @property
    async def status(self) -> Dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url=f'{WOLF_API}/{self.flow_id}', headers=self.auth_header
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientResponseError as e:
            if e.status == HTTPStatus.UNAUTHORIZED:
                _exit_error(
                    f'You are not authorized to access the Flow [b]{self.flow_id}[/b]'
                )

    async def list_all(self, status: Optional[str] = None) -> Dict:
        try:
            async with aiohttp.ClientSession() as session:
                _args = dict(url=WOLF_API, headers=self.auth_header)
                if status is not None and status != 'ALL':
                    _args['params'] = {'status': status}
                async with session.get(**_args) as response:
                    response.raise_for_status()
                    _results = await response.json()
                    if not _results:
                        print(
                            f'\nYou don\'t have any Flows deployed with status [green]{status}[/green]. '
                            f'Please pass a different [i]--status[/i] or use [i]jc deploy[/i] to deploy a new Flow'
                        )
                    return _results
        except aiohttp.ClientResponseError as e:
            if e.status == HTTPStatus.UNAUTHORIZED:
                _exit_error('Please login first.')
            elif e.status == HTTPStatus.NOT_FOUND:
                print(
                    '\nYou don\'t have any Flows deployed. Please use [b]jc deploy[/b]'
                )

    async def _upload_project(self, filepaths: List[Path], metadata: Dict = {}) -> str:
        data = aiohttp.FormData()
        data.add_field(name='metaData', value=json.dumps(metadata))
        [
            data.add_field(
                name='file', value=open(file.absolute(), 'rb'), filename=file.name
            )
            for file in filepaths
        ]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=ARTIFACT_API,
                data=data,
                headers=self.auth_header,
            ) as response:
                json_response = await response.json()
                _exit_if_response_error(response, HTTPStatus.OK)
                return json_response['data']['_id']

    async def _fetch_until(
        self,
        intermediate: List[Status],
        desired: Status = Status.ALIVE,
    ):
        _wait_seconds = 0
        _last_status = None
        while _wait_seconds < 600:
            _json_response = await self.status
            _current_status = Status(_json_response['status'])
            if _last_status is None:
                _last_status = _current_status

            if _current_status == desired:
                gateway = _json_response['gateway']
                logger.debug(
                    f'Successfully reached status: {desired} with gateway {gateway}'
                )
                return gateway
            elif _current_status not in intermediate:
                _exit_error(
                    f'Unexpected status: {_current_status} reached at [b]{_last_status}[/b].'
                )
            elif _current_status != _last_status:
                _last_status = _current_status
                pbar.update(
                    pb_task,
                    description=_current_status.value.title(),
                    advance=1,
                )
            else:
                await asyncio.sleep(1)
                _wait_seconds += 1

    async def _terminate(self):
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                url=f'{WOLF_API}/{self.flow_id}',
                headers=self.auth_header,
            ) as response:
                try:
                    json_response = await response.json()
                except json.decoder.JSONDecodeError:
                    _exit_error(
                        f'Can\'t find [b]{self.flow_id}[/b], check the ID or the flow may be removed already.'
                    )

                _exit_if_response_error(response, expected_status=HTTPStatus.ACCEPTED)

                self._t_logstream_task = asyncio.create_task(
                    CloudFlow.logstream(
                        params={'request_id': json_response['request_id']}
                    )
                )
                assert json_response['id'] == str(self.flow_id)
                assert Status(json_response['status']) == Status.SUBMITTED

    @staticmethod
    async def logstream(params):
        logger.debug(f'Asked to stream logs with params {params}')

        def dim_print(text):
            print(f'[dim]{text}[/dim]')

        log_msg = dim_print if 'request_id' in params else print

        try:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.ws_connect(LOGSTREAM_API, params=params) as ws:
                        logger.debug(
                            f'Successfully connected to logstream API with params: {params}'
                        )
                        await ws.send_json({})
                        async for msg in ws:
                            if msg.type == aiohttp.http.WSMsgType.TEXT:
                                log_dict: Dict = msg.json()
                                if log_dict.get('status') == 'STREAMING':
                                    log_msg(log_dict['message'])
                    logger.debug(f'Disconnected from the logstream server ...')
                except aiohttp.WSServerHandshakeError as e:
                    logger.critical(
                        f'Couldn\'t connect to the logstream server as {e!r}'
                    )
        except asyncio.CancelledError:
            logger.debug(f'Cancelling the logstreaming...')
        except Exception as e:
            logger.error(f'Got an exception while streaming logs {e!r}')

    async def __aenter__(self):
        with pbar:
            pbar.start_task(pb_task)
            pbar.update(
                pb_task,
                advance=1,
                description='Submitting',
                title=f'Deploying {self.path}',
            )
            await self._deploy()
            pbar.update(pb_task, description='Queueing (can take ~1 minute)', advance=1)
            self.gateway = await self._fetch_until(
                intermediate=[
                    Status.SUBMITTED,
                    Status.NORMALIZING,
                    Status.NORMALIZED,
                    Status.STARTING,
                ],
                desired=Status.ALIVE,
            )
            pbar.console.print(self)
            pbar.update(pb_task, description='Finishing', advance=1)
            self._c_logstream_task.cancel()

        if 'JCLOUD_NO_SURVEY' not in os.environ:
            # ask feedback
            from .auth import Survey

            Survey().count().ask(threshold=3)
        return self

    async def __aexit__(self, *args, **kwargs):
        with pbar:
            pbar.start_task(pb_task)
            pbar.update(
                pb_task,
                description='Submitting',
                advance=1,
                title=f'Removing flow {self.id}',
            )
            await self._terminate()
            pbar.update(pb_task, description='Queueing (can take ~1 minute)', advance=1)
            await self._fetch_until(
                intermediate=[Status.SUBMITTED, Status.DELETING],
                desired=Status.DELETED,
            )
            pbar.update(pb_task, description='Finishing', advance=1)
            self._t_logstream_task.cancel()
            await CloudFlow._cancel_pending()

    @staticmethod
    async def _cancel_pending():
        for task in asyncio.all_tasks():
            task.cancel()
            with suppress(asyncio.CancelledError, RuntimeError):
                await task

    def __enter__(self):
        return self._loop.run_until_complete(self.__aenter__())

    def __exit__(self, *args, **kwargs):
        self._loop.run_until_complete(self.__aexit__(*args, **kwargs))

    def __rich_console__(self, console, options):
        from rich import box
        from rich.panel import Panel
        from rich.table import Table

        my_table = Table(
            'Attribute', 'Value', show_header=False, box=box.SIMPLE, highlight=True
        )
        my_table.add_row('ID', self.id)
        my_table.add_row('URL', self.gateway)
        yield Panel(my_table, title=':tada: Flow is available!', expand=False)
