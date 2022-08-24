import asyncio
import json
import logging
import os
from contextlib import suppress
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiohttp
from rich import print
from hubble.utils.auth import Auth

from .constants import ARTIFACT_API, LOGSTREAM_API, WOLF_API, Status
from .helper import (
    get_logger,
    get_or_reuse_loop,
    get_pbar,
    normalized,
    zipdir,
)

logger = get_logger()

pbar, pb_task = get_pbar(
    '', total=5, disable='JCLOUD_NO_PROGRESSBAR' in os.environ
)  # progress bar for deployment


def _exit_if_response_error(
    response: aiohttp.ClientResponse, expected_status, json_response
):
    if response.status != expected_status:
        if response.status == HTTPStatus.FORBIDDEN:
            _exit_error(
                'You are not logged in, please login using [b]jcloud login[/b] first.'
            )
        else:
            _exit_error(
                f'Bad response: expecting [b]{expected_status}[/b], got [b]{response.status}[/b] from server.\n'
                f'{json.dumps(json_response, indent=1)}'
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

        token = Auth.get_auth_token()
        if not token:
            _exit_error(
                'You are not logged in, please login using [b]jcloud login[/b] first.'
            )
        else:
            self.auth_header = {'Authorization': f'token {token}'}

        if self.path is not None and not Path(self.path).exists():
            _exit_error(f'The path {self.path} specified doesn\'t exist.')

        if self.env_file is not None:
            if (
                not Path(self.env_file).exists()
                or not Path(self.env_file).is_file()
                or Path(self.env_file).suffix != '.env'
            ):
                _exit_error('The env_file specified isn\'t a valid .env file.')

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
            _tags.update({'envfile': _env_path.name})
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
            from dotenv import dotenv_values

            return dict(dotenv_values(_env_path))
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

        if _path.is_dir():
            _flow_path = _path / 'flow.yml'
            if _flow_path.exists() and normalized(_flow_path, self.envs):
                _data.add_field(name='yaml', value=open(_flow_path))
            else:
                params['artifactid'] = await self._zip_and_upload(_path)
        elif _path.is_file():
            if normalized(_path, self.envs):
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

        for i in range(2):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url=WOLF_API,
                        headers=self.auth_header,
                        **await self._get_post_params(),
                    ) as response:
                        json_response = await response.json()
                        _exit_if_response_error(
                            response,
                            expected_status=HTTPStatus.CREATED,
                            json_response=json_response,
                        )

                        if self.name:
                            assert self.name in json_response['name']
                        assert Status(json_response['status']) == Status.SUBMITTED

                        self.flow_id: str = json_response['id']
                        self.workspace_id: str = json_response['workspace']
                        self._request_id = json_response['request_id']

                        logger.debug(
                            f'POST /flows with flow_id {self.flow_id} & request_id {self._request_id}'
                        )

                        self._c_logstream_task = asyncio.create_task(
                            CloudFlow.logstream({'request_id': self._request_id})
                        )
                        return json_response
            except aiohttp.ClientConnectionError as e:
                if i == 0:
                    logger.debug(
                        'POST /flows at 1st attempt failed, will retry in 2s...'
                    )
                    await asyncio.sleep(2)
                else:
                    logger.debug('POST /flows retry failed too...')
                    raise e

    @property
    async def status(self) -> Dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url=f'{WOLF_API}/{self.flow_id}', headers=self.auth_header
                ) as response:
                    response.raise_for_status()
                    _results = await response.json()
                    return _results
        except aiohttp.ClientResponseError as e:
            if e.status == HTTPStatus.UNAUTHORIZED:
                _exit_error(
                    f'You are not authorized to access the Flow [b]{self.flow_id}[/b]'
                )
            if e.status == HTTPStatus.FORBIDDEN:
                _exit_error('Please login using [b]jc login[/b].')

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
            if e.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
                _exit_error('Please login using [b]jc login[/b].')
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
                _exit_if_response_error(
                    response,
                    expected_status=HTTPStatus.OK,
                    json_response=json_response,
                )
                return json_response['data']['_id']

    async def _fetch_until(
        self,
        intermediate: List[Status],
        desired: Status = Status.ALIVE,
    ) -> Tuple[Optional[str], Optional[Dict]]:
        _wait_seconds = 0
        _last_status = None
        while _wait_seconds < 1800:
            _json_response = await self.status
            if _json_response is None or 'status' not in _json_response:
                # intermittently no response is sent, retry then!
                continue
            _current_status = Status(_json_response['status'])
            if _last_status is None:
                _last_status = _current_status

            if _current_status == desired:
                gateway = _json_response.get('gateway', None)
                endpoints = _json_response.get('endpoints', {})
                logger.debug(
                    f'Successfully reached status: {desired} with gateway {gateway}'
                )
                return gateway, endpoints
            elif _current_status not in intermediate:
                _exit_error(
                    f'Unexpected status: {_current_status} reached at [b]{_last_status}[/b] '
                    f'for Flow ID [b]{self.id}[/b] with request_id [b]{self._request_id}[/b]'
                )
            elif _current_status != _last_status:
                _last_status = _current_status
                pbar.update(
                    pb_task,
                    description=_current_status.value.title(),
                    advance=1,
                )
            else:
                await asyncio.sleep(5)
                _wait_seconds += 5

        _exit_error(
            f'Couldn\'t reach status {desired} after waiting for 30mins. Exiting.'
        )

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

                _exit_if_response_error(
                    response,
                    expected_status=HTTPStatus.ACCEPTED,
                    json_response=json_response,
                )
                self._request_id = json_response['request_id']

                self._t_logstream_task = asyncio.create_task(
                    CloudFlow.logstream(params={'request_id': self._request_id})
                )
                assert json_response['id'] == str(self.flow_id)
                assert Status(json_response['status']) == Status.SUBMITTED

    @staticmethod
    async def logstream(params):
        logger.debug(f'Asked to stream logs with params {params}')

        def dim_print(text):
            print(f'[dim]{text}[/dim]')

        _log_fn = dim_print if 'request_id' in params else print
        _skip_debug_logs = (
            'request_id' in params and logger.getEffectiveLevel() >= logging.INFO
        )

        try:
            async with aiohttp.ClientSession() as session:
                _num_retries = 3
                for i in range(_num_retries):
                    # NOTE: Websocket endpoint has a default timeout of 15mins, after which connection drops.
                    # We'll retry the connection `_num_retries` times.
                    try:
                        async with session.ws_connect(
                            LOGSTREAM_API, params=params
                        ) as ws:
                            logger.debug(
                                f'Successfully connected to logstream API with params: {params}'
                            )
                            await ws.send_json({})
                            async for msg in ws:
                                if msg.type == aiohttp.http.WSMsgType.TEXT:
                                    log_dict: Dict = msg.json()
                                    if log_dict.get('status') == 'STREAMING':
                                        if _skip_debug_logs:
                                            continue
                                        _log_fn(log_dict['message'])
                        logger.debug(
                            f'Disconnected from the logstream server ... '
                            + 'Retrying ..'
                            if i <= _num_retries
                            else ''
                        )
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
                title=f'Deploying {self.name or Path(self.path).resolve()}',
            )
            await self._deploy()
            pbar.update(pb_task, description='Queueing (can take ~1 minute)', advance=1)
            self.gateway, self.endpoints = await self._fetch_until(
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
            from .survey import Survey

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
        if self.gateway is not None:
            my_table.add_row('Endpoint(s)', self.gateway)
        elif self.endpoints:
            for k, v in self.endpoints.items():
                my_table.add_row(k, v)
        yield Panel(my_table, title=':tada: Flow is available!', expand=False)


async def _terminate_flow_simplified(flow_id):
    """Terminate a Flow given flow_id.

    This is a simplified version of CloudFlow.__aexit__, i.e.,
    without reporting the details of the termination process using the progress bar.
    It's supposed to be used in the multi-flow removal context.
    """

    flow = CloudFlow(flow_id=flow_id)
    await flow._terminate()
    await flow._fetch_until(
        intermediate=[Status.SUBMITTED, Status.DELETING],
        desired=Status.DELETED,
    )
    flow._t_logstream_task.cancel()

    # This needs to be returned so in asyncio.as_completed, it can be printed.
    return flow_id
