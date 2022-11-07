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
from hubble.utils.auth import Auth
from rich import print

from .constants import (
    ARTIFACT_API,
    FLOWS_API,
    JCLOUD_API,
    Phase,
    get_phase_from_response,
)
from .helper import get_logger, get_or_reuse_loop, get_pbar, normalized, zipdir

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
    flow_id: Optional[str] = None

    def __post_init__(self):

        token = Auth.get_auth_token()
        if not token:
            _exit_error(
                'You are not logged in, please login using [b]jcloud login[/b] first.'
            )
        else:
            self.auth_header = {'Authorization': token}

        if self.path is not None and not Path(self.path).exists():
            _exit_error(f'The path {self.path} specified doesn\'t exist.')

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
        _data = aiohttp.FormData()
        _path = Path(self.path)

        if _path.is_dir():
            _flow_path = _path / 'flow.yml'
            if _flow_path.exists() and normalized(_flow_path):
                _data.add_field(name='spec', value=open(_flow_path))
            else:
                _exit_error("Normalization of Flows not supported yet")
        elif _path.is_file():
            if normalized(_path):
                _data.add_field(name='spec', value=open(_path))
            else:
                _exit_error("Normalization of Flows not supported yet")

        if _data._fields:
            _post_kwargs['data'] = _data
        _post_kwargs['params'] = params
        return _post_kwargs

    async def _deploy(self):

        for i in range(2):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url=FLOWS_API,
                        headers=self.auth_header,
                        **await self._get_post_params(),
                    ) as response:
                        json_response = await response.json()
                        _exit_if_response_error(
                            response,
                            expected_status=HTTPStatus.CREATED,
                            json_response=json_response,
                        )

                        assert Phase(json_response['status']) == Phase.SUBMITTED

                        self.flow_id: str = json_response['id']

                        logger.debug(
                            f'POST /flows with flow_id {self.flow_id} & request_id {self._request_id}'
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
                    url=f'{FLOWS_API}/{self.flow_id}', headers=self.auth_header
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientResponseError as e:
            if e.status == HTTPStatus.UNAUTHORIZED:
                _exit_error(
                    f'You are not authorized to access the Flow [b]{self.flow_id}[/b]'
                )
            if e.status == HTTPStatus.FORBIDDEN:
                _exit_error('Please login using [b]jc login[/b].')

    async def list_all(
        self,
        phase: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Dict:
        try:
            async with aiohttp.ClientSession() as session:
                _args = dict(url=FLOWS_API, headers=self.auth_header)
                _args['params'] = {}

                if phase is not None and phase != 'All':
                    _args['params'].update({'phase': phase})
                if name is not None:
                    _args['params'].update({'name': name})

                async with session.get(**_args) as response:
                    response.raise_for_status()
                    _results = await response.json()
                    if not _results:
                        print(
                            f'\nYou don\'t have any Flows deployed with status [green]{phase}[/green]. '
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
        intermediate: List[Phase],
        desired: Phase = Phase.Serving,
    ) -> Tuple[Optional[str], Optional[Dict]]:
        _wait_seconds = 0
        _last_phase = None
        while _wait_seconds < 1800:
            _json_response = await self.status
            if _json_response is None or 'status' not in _json_response:
                # intermittently no response is sent, retry then!
                continue
            _current_phase = get_phase_from_response(_json_response)

            if _last_phase is None:
                _last_phase = _current_phase

            if _current_phase == desired:
                gateway = _json_response.get('gateway', None)
                endpoints = _json_response.get('endpoints', {})
                dashboard = _json_response.get('dashboards', {}).get('monitoring', None)
                logger.debug(
                    f'Successfully reached phase: {desired} with gateway {gateway}'
                )
                return gateway, endpoints, dashboard
            elif _current_phase not in intermediate:
                _exit_error(
                    f'Unexpected phase: {_current_phase} reached at [b]{_last_phase}[/b] '
                    f'for Flow ID [b]{self.id}[/b]'
                )
            elif _current_phase != _last_phase:
                _last_phase = _current_phase
                pbar.update(
                    pb_task,
                    description=_current_phase.value.title(),
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
                url=f'{JCLOUD_API}/{self.flow_id}',
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
                    expected_status=HTTPStatus.OK,
                    json_response=json_response,
                )
                assert Phase(json_response['status']) == Phase.SUBMITTED

    async def __aenter__(self):
        with pbar:
            pbar.start_task(pb_task)
            pbar.update(
                pb_task,
                advance=1,
                description='Submitting',
                title=f'Deploying {Path(self.path).resolve()}',
            )
            await self._deploy()
            pbar.update(pb_task, description='Queueing (can take ~1 minute)', advance=1)
            self.gateway, self.endpoints, self.dashboard = await self._fetch_until(
                intermediate=[
                    Phase.SUBMITTED,
                    Phase.NORMALIZING,
                    Phase.NORMALIZED,
                    Phase.STARTING,
                ],
                desired=Phase.ALIVE,
            )
            pbar.console.print(self)
            pbar.update(pb_task, description='Finishing', advance=1)

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
                intermediate=[Phase.SUBMITTED, Phase.DELETING],
                desired=Phase.DELETED,
            )
            pbar.update(pb_task, description='Finishing', advance=1)
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
        if self.dashboard is not None:
            my_table.add_row('Dashboard', self.dashboard)
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
        intermediate=[Phase.SUBMITTED, Phase.DELETING],
        desired=Phase.DELETED,
    )

    # This needs to be returned so in asyncio.as_completed, it can be printed.
    return flow_id
