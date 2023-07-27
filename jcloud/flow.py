import asyncio
import json
import yaml
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
    FLOWS_API,
    JOBS_API,
    SECRETS_API,
    CustomAction,
    Phase,
    Resources,
    get_phase_from_response,
    DASHBOARD_URL_MARKDOWN,
    DASHBOARD_URL_LINK,
)
from .helper import (
    get_aiohttp_session,
    get_endpoints_from_response,
    get_logger,
    get_or_reuse_loop,
    get_pbar,
    normalized,
    update_flow_yml_and_write_to_file,
    get_filename_envs,
    validate_flow_yaml_exists,
    load_flow_data,
    exit_error,
)

logger = get_logger()

pbar, pb_task = get_pbar(
    '', total=2, disable='JCLOUD_NO_PROGRESSBAR' in os.environ
)  # progress bar for deployment


def _exit_if_response_error(
    response: aiohttp.ClientResponse, expected_status, json_response
):
    if response.status != expected_status:
        if response.status == HTTPStatus.UNAUTHORIZED:
            print(
                f'[red]You are not logged in, please login using [b]jcloud login[/b] first.[/red]'
            )
        elif response.status == HTTPStatus.FORBIDDEN:
            print_server_resposne(json_response['error'])
            exit_error(
                f'Please make sure your account is activated and funded or that you own the requested flow.'
            )
        elif response.status == HTTPStatus.NOT_FOUND:
            print_server_resposne(json_response['error'])
            exit_error(f'Please make sure the requested resource exists.')
        else:
            exit_error(
                f'Bad response: expecting [b]{expected_status}[/b], got [b]{response.status}[/b] from server.\n'
                f'{json.dumps(json_response, indent=1)}'
            )


def print_server_resposne(error_message: str):
    print(f'Got an error from the server: [red]{error_message}[/red]')


def get_resource_url(resource: str) -> str:
    if Resources.Job in resource:
        return JOBS_API
    return SECRETS_API


@dataclass
class CloudFlow:
    path: Optional[str] = None
    flow_id: Optional[str] = None
    # by default flow will be available at the end of an operation
    # it will be modified accordingly, if not available
    flow_status = 'available'

    def __post_init__(self):
        token = Auth.get_auth_token()
        if not token:
            exit_error(
                'You are not logged in, please login using [b]jcloud login[/b] first.'
            )
        else:
            self.auth_header = {'Authorization': token}

        if self.path is not None and not Path(self.path).exists():
            exit_error(f'The path {self.path} specified doesn\'t exist.')

    @property
    def id(self) -> str:
        return self.flow_id.split('-')[1]

    @property
    def _loop(self):
        return get_or_reuse_loop()

    async def _get_post_params(self, from_validate: Optional[bool] = False):
        from jcloud.normalize import flow_normalize

        params, _post_kwargs = {}, {}
        _data = aiohttp.FormData()
        _flow_path = Path(self.path)

        if _flow_path.is_dir():
            _flow_path = _flow_path / 'flow.yml'

        validate_flow_yaml_exists(_flow_path)
        if not normalized(_flow_path):
            _flow_path = flow_normalize(
                _flow_path, output_path=_flow_path if from_validate else None
            )
            _data.add_field(name='spec', value=open(_flow_path))
        else:
            _flow_dict = load_flow_data(
                _flow_path, get_filename_envs(_flow_path.parent)
            )
            _data.add_field(
                name='spec', value=yaml.dump(_flow_dict, sort_keys=False).encode()
            )

        if _data._fields:
            _post_kwargs['data'] = _data
        _post_kwargs['params'] = params
        return _post_kwargs

    async def validate(self):
        try:
            async with get_aiohttp_session() as session:
                async with session.post(
                    url=FLOWS_API + '/validate',
                    headers=self.auth_header,
                    **await self._get_post_params(from_validate=True),
                ) as response:
                    json_response = await response.json()
                    response.raise_for_status()
                    return json_response
        except aiohttp.ClientResponseError:
            _exit_if_response_error(
                response,
                expected_status=HTTPStatus.OK,
                json_response=json_response,
            )

    async def _deploy(self):
        _validate_resposne = await self.validate()
        if len(_validate_resposne['errors']) == 0:
            logger.info(
                f'Successfully validated flow config. Proceeding to flow deployment...'
            )
        else:
            errors = '\n'.join(_validate_resposne['errors'])
            exit_error(
                f'Found {len(_validate_resposne["errors"])} error(s) in Flow config.\n{errors}'
            )
        for i in range(2):
            try:
                async with get_aiohttp_session() as session:
                    async with session.post(
                        url=FLOWS_API,
                        headers=self.auth_header,
                        **await self._get_post_params(),
                    ) as response:
                        json_response = await response.json()
                        response.raise_for_status()
                        self.flow_id: str = json_response['id']
                        logger.info(
                            f'Successfully submitted flow with ID [bold][blue]{self.flow_id}[/blue][/bold]'
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
            except aiohttp.ClientResponseError as e:
                if e.status == HTTPStatus.SERVICE_UNAVAILABLE and i == 0:
                    logger.debug(
                        'POST /flows at 1st attempt failed, will retry in 2s...'
                    )
                    await asyncio.sleep(2)
                else:
                    _exit_if_response_error(
                        response,
                        expected_status=HTTPStatus.CREATED,
                        json_response=json_response,
                    )

    async def update(self):
        async def _update():
            for i in range(2):
                try:
                    async with get_aiohttp_session() as session:
                        api_url = FLOWS_API + "/" + self.flow_id
                        post_params = await self._get_post_params()

                        async with session.put(
                            url=api_url,
                            headers=self.auth_header,
                            **post_params,
                        ) as response:
                            json_response = await response.json()
                            _exit_if_response_error(
                                response,
                                expected_status=HTTPStatus.ACCEPTED,
                                json_response=json_response,
                            )

                            if self.flow_id is not json_response['id']:
                                # TODO: is this validation needed?
                                pass

                            logger.info(
                                f'Successfully submitted flow with ID [bold][blue]{self.flow_id}[/blue][/bold] to get updated'
                            )
                            return json_response
                except aiohttp.ClientConnectionError as e:
                    if i == 0:
                        logger.debug(
                            f'PUT /flows/{self.flow_id} at 1st attempt failed, will retry in 2s...'
                        )
                        await asyncio.sleep(2)
                    else:
                        logger.debug(f'PUT /flows/{self.flow_id} retry failed too...')
                        raise e

        with pbar:
            desired_phase = Phase.Serving
            title = f'Updating {Path(self.path).resolve()}'

            pbar.start_task(pb_task)
            pbar.update(
                pb_task,
                advance=1,
                description='Submitting',
                title=title,
            )
            await _update()
            logger.info(f'Check the Flow deployment logs: {await self.jcloud_logs} !')
            self.endpoints, self.dashboard = await self._fetch_until(
                intermediate=[
                    Phase.Empty,
                    Phase.Pending,
                    Phase.Updating,
                ],
                desired=desired_phase,
            )
            if 'JCLOUD_HIDE_SUCCESS_MSG' not in os.environ:
                pbar.console.print(self)
            pbar.update(pb_task, description='Finishing', advance=1)

    async def custom_action(
        self, cust_act: CustomAction = CustomAction.NoAction, **kwargs
    ):
        if cust_act == CustomAction.NoAction:
            logger.error("no custom action specified")
            return

        if cust_act not in [
            CustomAction.Restart,
            CustomAction.Pause,
            CustomAction.Resume,
            CustomAction.Scale,
            CustomAction.Recreate,
        ]:
            logger.error("invalid custom action specified")
            return

        async def _custom_action(api_url):
            for i in range(2):
                try:
                    async with get_aiohttp_session() as session:
                        post_params = dict()

                        async with session.put(
                            url=api_url,
                            headers=self.auth_header,
                            **post_params,
                        ) as response:
                            json_response = await response.json()
                            _exit_if_response_error(
                                response,
                                expected_status=HTTPStatus.ACCEPTED,
                                json_response=json_response,
                            )

                            logger.info(
                                f'Successfully submitted flow with ID [bold][blue]{self.flow_id}[/blue][/bold]'
                            )
                            return json_response
                except aiohttp.ClientConnectionError as e:
                    if i == 0:
                        logger.debug(
                            f'PUT /flows/{self.flow_id} at 1st attempt failed, will retry in 2s...'
                        )
                        await asyncio.sleep(2)
                    else:
                        logger.debug(f'PUT /flows/{self.flow_id} retry failed too...')
                        raise e

        with pbar:
            desired_phase = Phase.Serving
            if cust_act is CustomAction.Restart:
                title = 'Restarting the Flow'
                api_url = FLOWS_API + "/" + self.flow_id + ":" + CustomAction.Restart
                if kwargs.get('gateway', False):
                    title = 'Restarting gateway of the Flow'
                    api_url = (
                        FLOWS_API
                        + "/"
                        + self.flow_id
                        + "/gateway"
                        + ":"
                        + CustomAction.Restart
                    )
                elif kwargs.get('executor', None):
                    exc = kwargs['executor']
                    title = f'Restarting executor:{exc} of the Flow'
                    api_url = (
                        FLOWS_API
                        + "/"
                        + self.flow_id
                        + "/executors/"
                        + exc
                        + ":"
                        + CustomAction.Restart
                    )
            elif cust_act == CustomAction.Pause:
                desired_phase = Phase.Paused
                title = 'Pausing the Flow'
                api_url = FLOWS_API + "/" + self.flow_id + ":" + CustomAction.Pause
            elif cust_act == CustomAction.Resume:
                title = 'Resuming the Flow'
                api_url = FLOWS_API + "/" + self.flow_id + ":" + CustomAction.Resume
            elif cust_act == CustomAction.Scale:
                title = 'Scaling Executor in Flow'
                api_url = (
                    FLOWS_API
                    + '/'
                    + self.flow_id
                    + '/executors/'
                    + kwargs['executor']
                    + ':'
                    + CustomAction.Scale
                    + f'?replicas={kwargs["replicas"]}'
                )
            elif cust_act == CustomAction.Recreate:
                desired_phase = Phase.Serving
                title = 'Recreating the deleted Flow'
                api_url = FLOWS_API + '/' + self.flow_id + ':' + CustomAction.Recreate

            pbar.start_task(pb_task)
            pbar.update(
                pb_task,
                advance=1,
                description='Submitting',
                title=title,
            )
            await _custom_action(api_url=api_url)
            logger.info(f'Check the Flow deployment logs: {await self.jcloud_logs} !')
            self.endpoints, self.dashboard = await self._fetch_until(
                intermediate=[
                    Phase.Empty,
                    Phase.Pending,
                    Phase.Updating,
                    Phase.Starting,
                ],
                desired=desired_phase,
            )
            if 'JCLOUD_HIDE_SUCCESS_MSG' not in os.environ:
                pbar.console.print(self)
            pbar.update(pb_task, description='Finishing', advance=1)

    async def restart(self, gateway: bool = False, executor: str = None):
        await self.custom_action(
            CustomAction.Restart, gateway=gateway, executor=executor
        )

    async def pause(self):
        self.flow_status = "paused"
        await self.custom_action(CustomAction.Pause)

    async def resume(self):
        await self.custom_action(CustomAction.Resume)

    async def scale(self, executor, replicas):
        await self.custom_action(
            CustomAction.Scale, executor=executor, replicas=replicas
        )

    async def recreate(self):
        await self.custom_action(CustomAction.Recreate)

    @property
    async def jcloud_logs(self) -> str:
        return DASHBOARD_URL_LINK.format(flow_id=self.flow_id)

    @property
    async def status(self) -> Dict:
        async with get_aiohttp_session() as session:
            async with session.get(
                url=f'{FLOWS_API}/{self.flow_id}', headers=self.auth_header
            ) as response:
                json_response = await response.json()
                _exit_if_response_error(
                    response,
                    expected_status=HTTPStatus.OK,
                    json_response=json_response,
                )
                return await response.json()

    async def logs(self, executor_name: Optional[str] = None) -> Dict:
        _base_url = f'{FLOWS_API}/{self.flow_id}'
        if executor_name:
            _url = f'{_base_url}/executors/{executor_name}'
        else:
            _url = f'{_base_url}/gateway'
        async with get_aiohttp_session() as session:
            async with session.get(
                url=f'{_url}/logs', headers=self.auth_header
            ) as response:
                json_response = await response.json()
                _exit_if_response_error(
                    response,
                    expected_status=HTTPStatus.OK,
                    json_response=json_response,
                )
                return json_response['logs']

    async def job_logs(self, job_name: str) -> str:
        async with get_aiohttp_session() as session:
            async with session.get(
                url=f'{JOBS_API}/{self.flow_id}/{job_name}/logs',
                headers=self.auth_header,
            ) as response:
                json_response = await response.json()
                _exit_if_response_error(
                    response,
                    expected_status=HTTPStatus.OK,
                    json_response=json_response,
                )
                return json_response['logs']

    async def create_job(
        self,
        job_name: str,
        image_name: str,
        timeout: Optional[int],
        backofflimit: Optional[int],
        entrypoint: Optional[str] = "",
    ):
        json_object = {
            'name': job_name,
            'image': image_name,
            'timeout': timeout,
            'backoffLimit': backofflimit,
            'entrypoint': entrypoint,
            'flowid': self.flow_id,
        }
        async with get_aiohttp_session() as session:
            async with session.post(
                url=JOBS_API,
                headers=self.auth_header,
                json=json_object,
            ) as response:
                json_response = await response.json()
                _exit_if_response_error(
                    response,
                    expected_status=HTTPStatus.CREATED,
                    json_response=json_response,
                )
                return json_response

    async def create_secret(
        self,
        secret_name: str,
        env_secret_data: Dict,
        update: bool = False,
    ) -> Dict:
        json_object = {
            'name': secret_name,
            'id': self.flow_id,
            'data': env_secret_data,
        }
        logger.info(f'Creating Secret {secret_name} for flow {self.flow_id}')
        async with get_aiohttp_session() as session:
            async with session.post(
                url=SECRETS_API,
                headers=self.auth_header,
                json=json_object,
            ) as response:
                json_response = await response.json()
                _exit_if_response_error(
                    response,
                    expected_status=HTTPStatus.CREATED,
                    json_response=json_response,
                )
        logger.info(f'Secret {secret_name} created for flow {self.flow_id}')
        if update:
            if not self.path:
                self.path = os.path.curdir
            _flow_path = Path(self.path)
            if _flow_path.is_dir():
                _flow_path = _flow_path / 'flow.yml'
            self.path = update_flow_yml_and_write_to_file(
                _flow_path,
                secret_name,
                env_secret_data,
            )
            logger.info('Updating Flow spec with Secret data...')
            await self.update()
        return json_response

    async def update_secret(
        self, secret_name: str, secret_data: Dict, update: bool = False
    ) -> Dict:
        json_object = {
            'name': secret_name,
            'id': self.flow_id,
            'data': secret_data,
        }
        logger.info(f'Updating Secret {secret_name} for flow {self.flow_id}')
        async with get_aiohttp_session() as session:
            async with session.post(
                url=f'{SECRETS_API}/{self.flow_id}/{secret_name}',
                headers=self.auth_header,
                json=json_object,
            ) as response:
                json_response = await response.json()
                _exit_if_response_error(
                    response,
                    expected_status=HTTPStatus.CREATED,
                    json_response=json_response,
                )
        logger.info(f'Secret {secret_name} Updated for flow {self.flow_id}')
        if update:
            if not self.path:
                self.path = os.path.curdir
            _flow_path = Path(self.path)
            if _flow_path.is_dir():
                _flow_path = _flow_path / 'flow.yml'
            self.path = update_flow_yml_and_write_to_file(
                _flow_path,
                secret_name,
                secret_data,
            )
            logger.info('Updating Flow spec with Secret data...')
            await self.update()
        logger.info('Restarting Flow to update Secret data...')
        await self.restart()
        return json_response

    async def get_resource(self, resource: Dict, resource_name: Dict) -> Dict:
        url = get_resource_url(resource)
        async with get_aiohttp_session() as session:
            async with session.get(
                url=f'{url}/{self.flow_id}/{resource_name}',
                headers=self.auth_header,
            ) as response:
                json_response = await response.json()
                _exit_if_response_error(
                    response,
                    expected_status=HTTPStatus.OK,
                    json_response=json_response,
                )
                return json_response

    async def list_resources(self, resource: str) -> List:
        url = get_resource_url(resource)
        async with get_aiohttp_session() as session:
            async with session.get(
                url=f'{url}/{self.flow_id}',
                headers=self.auth_header,
            ) as response:
                json_response = await response.json()
                _exit_if_response_error(
                    response,
                    expected_status=HTTPStatus.OK,
                    json_response=json_response,
                )
                key = (
                    f'{Resources.Job}s'
                    if Resources.Job in resource
                    else f'{Resources.Secret}s'
                )
                return json_response[key]

    async def delete_resource(self, resource: str, resource_name: str):
        url = get_resource_url(resource)
        async with get_aiohttp_session() as session:
            async with session.delete(
                url=f'{url}/{self.flow_id}/{resource_name}',
                headers=self.auth_header,
            ) as response:
                json_response = await response.json()
                _exit_if_response_error(
                    response,
                    expected_status=HTTPStatus.OK,
                    json_response=json_response,
                )

    async def list_all(
        self,
        phase: Optional[str] = None,
        name: Optional[str] = None,
        labels: Dict[str, str] = None,
    ) -> Dict:
        async with get_aiohttp_session() as session:
            _args = dict(url=FLOWS_API, headers=self.auth_header)
            _args['params'] = {}

            if phase is not None and phase != 'All':
                _args['params'].update({'phase': phase})
            if name is not None:
                _args['params'].update({'name': name})
            if labels is not None:
                _args['params'].update({'labels': labels})
            async with session.get(**_args) as response:
                _results = await response.json()
                if not _results:
                    print(
                        f'\nYou don\'t have any Flows deployed with status [green]{phase}[/green]. '
                        f'Please pass a different [i]--status[/i] or use [i]jc deploy[/i] to deploy a new Flow'
                    )
                _exit_if_response_error(
                    response,
                    expected_status=HTTPStatus.OK,
                    json_response=_results,
                )
                return _results

    async def _fetch_until(
        self,
        intermediate: List[Phase],
        desired: Phase = Phase.Serving,
    ) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
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
                logger.debug(f'Successfully reached phase: {desired}')
                return (
                    get_endpoints_from_response(_json_response),
                    DASHBOARD_URL_MARKDOWN.format(flow_id=self.flow_id),
                )
            elif _current_phase not in intermediate:
                exit_error(
                    f'Unexpected phase: {_current_phase} reached at [b]{_last_phase}[/b] '
                    f'for Flow ID [b]{self.flow_id}[/b]'
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

        exit_error(
            f'Couldn\'t reach status {desired} after waiting for 30mins. Exiting.'
        )

    async def _terminate(self):
        async with get_aiohttp_session() as session:
            async with session.delete(
                url=f'{FLOWS_API}/{self.flow_id}',
                headers=self.auth_header,
            ) as response:
                try:
                    json_response = await response.json()
                except json.decoder.JSONDecodeError:
                    exit_error(
                        f'Can\'t find [b]{self.flow_id}[/b], check the ID or the flow may be removed already.'
                    )

                _exit_if_response_error(
                    response,
                    expected_status=HTTPStatus.OK,
                    json_response=json_response,
                )

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
            logger.info(f'Check the Flow deployment logs: {await self.jcloud_logs} !')
            self.endpoints, self.dashboard = await self._fetch_until(
                intermediate=[
                    Phase.Empty,
                    Phase.Pending,
                    Phase.Starting,
                ],
                desired=Phase.Serving,
            )
            if 'JCLOUD_HIDE_SUCCESS_MSG' not in os.environ:
                pbar.console.print(self)
            pbar.update(pb_task, description='Finishing', advance=1)

        return self

    async def __aexit__(self, *args, **kwargs):
        with pbar:
            pbar.start_task(pb_task)
            pbar.update(
                pb_task,
                description='Submitting',
                advance=1,
                title=f'Removing flow {self.flow_id}',
            )
            await self._terminate()
            await self._fetch_until(
                intermediate=[Phase.Serving],
                desired=Phase.Deleted,
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
        from rich.markdown import Markdown

        my_table = Table(
            'Attribute', 'Value', show_header=False, box=box.SIMPLE, highlight=True
        )
        my_table.add_row('ID', self.flow_id)
        if self.endpoints:
            for k, v in self.endpoints.items():
                my_table.add_row(k.title(), v)
        if self.dashboard is not None:
            my_table.add_row('Dashboard', Markdown(self.dashboard))
        yield Panel(
            my_table,
            title=f':tada: Flow is {self.flow_status}!',
            expand=False,
            width=100,
        )


async def _terminate_flow_simplified(flow_id: str, phase: Optional[str] = None):
    """Terminate a Flow given flow_id.

    This is a simplified version of CloudFlow.__aexit__, i.e.,
    without reporting the details of the termination process using the progress bar.
    It's supposed to be used in the multi-flow removal context.
    """

    flow = CloudFlow(flow_id=flow_id)
    await flow._terminate()
    _intermediate_phases = [Phase.Serving]
    if phase is not None:
        _intermediate_phases.append(phase)
    await flow._fetch_until(
        intermediate=_intermediate_phases,
        desired=Phase.Deleted,
    )

    # This needs to be returned so in asyncio.as_completed, it can be printed.
    return flow_id
