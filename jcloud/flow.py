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


from . import AUTH_HEADERS, LOGSTREAM_API, WOLF_API
from .helper import get_logger, get_or_reuse_loop, get_pbar, upload_project, zipdir


WOLF_API = 'https://api.wolf.jina.ai/dev/flows'
LOGSTREAM_API = 'wss://logs.wolf.jina.ai/dev/'

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


def _raise_response_error(response, expected_status):
    if response.status != expected_status:
        if response.status == HTTPStatus.FORBIDDEN:
            print(
                '[red][b]WOLF_TOKEN[/b] is not valid. Please check or login again.[/red]'
            )
        else:
            print(f'[red]Something wrong, got {response.status} from server.[/red]')
        exit(1)


@dataclass
class CloudFlow:
    path: Optional[str] = None
    name: Optional[str] = None
    workspace_id: Optional[str] = None
    flow_id: Optional[str] = None
    artifactid: Optional[str] = None

    def __post_init__(self):
        from .auth import Auth

        # check auth header
        # if 'WOLF_TOKEN' not in os.environ:
        #     print('[red][b]WOLF_TOKEN[/b] can not be found, please login first.[/red]')
        token = Auth.get_auth_token()
        if not token:
            print('[red]You are not [b]logged in[/b], please login first.[/red]')
            exit(1)
        else:
            # self.auth_header = {'Authorization': os.environ['WOLF_TOKEN']}
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

    async def zip_and_upload(self):
        with zipdir(directory=Path(self.path)) as zipfilepath:
            self.artifactid = await upload_project(filepaths=[zipfilepath])

    async def _deploy(self):
        params = {}
        if self.name:
            params['name'] = self.name
        if self.workspace_id:
            params['workspace'] = self.workspace_id

        async with aiohttp.ClientSession() as session:
            _post_kwargs = dict(url=WOLF_API, headers=AUTH_HEADERS)
            _path = Path(self.path)
            if not _path.exists():
                logger.error(f'Path {self.path} doesn\'t exist. Cannot deploy the Flow')
            elif _path.is_dir():
                await self.zip_and_upload()
                params['artifactid'] = self.artifactid
            elif _path.is_file():
                _post_kwargs['data'] = {'yaml': open(self.path)}

            _post_kwargs['params'] = params
            async with session.post(**_post_kwargs) as response:
                json_response = await response.json()
                _raise_response_error(response, HTTPStatus.CREATED)

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
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f'{WOLF_API}/{self.flow_id}', headers=self.auth_header
            ) as response:
                response.raise_for_status()
                return await response.json()

    @staticmethod
    async def list_all():
        async with aiohttp.ClientSession() as session:
            async with session.get(url=WOLF_API) as response:
                response.raise_for_status()
                return await response.json()

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
            elif _last_status != _current_status:
                _last_status = _current_status
                pbar.update(
                    pb_task,
                    description=_current_status.value.title(),
                    advance=1,
                )

            if _current_status == desired:
                gateway = _json_response['gateway']
                logger.debug(
                    f'Successfully reached status: {desired} with gateway {gateway}'
                )
                return gateway
            else:
                assert _current_status in intermediate
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
                    print(
                        f'[red]Can\'t find [b]{self.flow_id}[/b], check the ID or the flow may be removed already.[/red]'
                    )
                    exit(1)
                _raise_response_error(response, expected_status=HTTPStatus.ACCEPTED)

                self._t_logstream_task = asyncio.create_task(
                    CloudFlow.logstream(
                        params={'request_id': json_response['request_id']}
                    )
                )
                assert json_response['id'] == str(self.flow_id)
                assert Status(json_response['status']) == Status.DELETING

    @staticmethod
    async def logstream(params):
        logger.debug(f'Asked to stream logs with params {params}')

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
                                    logger.info(log_dict['message'])
                    logger.debug(f'Disconnected from the logstream server ...')
                except aiohttp.WSServerHandshakeError as e:
                    logger.critical(
                        f'Couldn\'t connect to the logstream server as {e!r}'
                    )
        except asyncio.CancelledError:
            logger.debug(f'logstream task cancelled.')
        except Exception as e:
            logger.error(f'Got an exception while streaming logs {e!r}')

    async def __aenter__(self):
        with pbar:
            pbar.start_task(pb_task)
            pbar.update(
                pb_task, advance=1, description='Submitting', title='Deploying the flow'
            )
            await self._deploy()
            pbar.update(pb_task, description='Queueing', advance=1)
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
            return self

    async def __aexit__(self, *args, **kwargs):
        with pbar:
            pbar.start_task(pb_task)
            pbar.update(
                pb_task,
                description='Submitting',
                advance=1,
                title=f'Remove flow {self.id}',
            )
            await self._terminate()
            pbar.update(pb_task, description='Queueing', advance=1)
            await self._fetch_until(
                intermediate=[Status.DELETING],
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
