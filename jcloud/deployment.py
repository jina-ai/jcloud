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
    DEPLOYMENTS_API,
    CustomAction,
    Phase,
    Resources,
    get_phase_from_response,
    DASHBOARD_DEPLOYMENT_URL_MARKDOWN,
    DASHBOARD_DEPLOYMENT_URL_LINK,
)
from .helper import (
    get_aiohttp_session,
    get_endpoints_from_response,
    get_logger,
    get_or_reuse_loop,
    get_pbar,
    normalized,
    update_deployment_yml_and_write_to_file,
    get_filename_envs,
    validate_yaml_exists,
    load_deployment_data,
    exit_error,
    _exit_if_response_error,
)

logger = get_logger()

pbar, pb_task = get_pbar(
    '', total=2, disable='JCLOUD_NO_PROGRESSBAR' in os.environ
)  # progress bar for deployment


@dataclass
class CloudDeployment:
    path: Optional[str] = None
    deployment_id: Optional[str] = None
    # by default deployment will be available at the end of an operation
    # it will be modified accordingly, if not available
    deployment_status = 'available'

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
        return self.deployment_id.split('-')[1]

    @property
    def _loop(self):
        return get_or_reuse_loop()

    async def _get_post_params(self, from_validate: Optional[bool] = False):
        # TODO (Subbu) Normalization
        # from jcloud.normalize import deployment_normalize

        params, _post_kwargs = {}, {}
        _data = aiohttp.FormData()
        _deployment_path = Path(self.path)

        if _deployment_path.is_dir():
            _deployment_path = _deployment_path / 'deployment.yml'

        validate_yaml_exists(_deployment_path)
        if not normalized(_deployment_path):
            pass
            # TODO (Subbu) Normalization
            # _deployment_path = deployment_normalize(
            #     _deployment_path, output_path=_deployment_path if from_validate else None
            # )
            # _data.add_field(name='spec', value=open(_deployment_path))
        else:
            _deployment_dict = load_deployment_data(
                _deployment_path, get_filename_envs(_deployment_path.parent)
            )
            _data.add_field(
                name='spec', value=yaml.dump(_deployment_dict, sort_keys=False).encode()
            )

        if _data._fields:
            _post_kwargs['data'] = _data
        _post_kwargs['params'] = params
        return _post_kwargs

    async def validate(self):
        try:
            async with get_aiohttp_session() as session:
                async with session.post(
                    url=DEPLOYMENTS_API + '/validate',
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
                f'Successfully validated deployment config. Proceeding to deployment deployment...'
            )
        else:
            errors = '\n'.join(_validate_resposne['errors'])
            exit_error(
                f'Found {len(_validate_resposne["errors"])} error(s) in Deployment config.\n{errors}'
            )
        for i in range(2):
            try:
                async with get_aiohttp_session() as session:
                    async with session.post(
                        url=DEPLOYMENTS_API,
                        headers=self.auth_header,
                        **await self._get_post_params(),
                    ) as response:
                        json_response = await response.json()
                        response.raise_for_status()
                        self.deployment_id: str = json_response['id']
                        logger.info(
                            f'Successfully submitted deployment with ID [bold][blue]{self.deployment_id}[/blue][/bold]'
                        )
                        return json_response
            except aiohttp.ClientConnectionError as e:
                if i == 0:
                    logger.debug(
                        'POST /deployments at 1st attempt failed, will retry in 2s...'
                    )
                    await asyncio.sleep(2)
                else:
                    logger.debug('POST /deployments retry failed too...')
                    raise e
            except aiohttp.ClientResponseError as e:
                if e.status == HTTPStatus.SERVICE_UNAVAILABLE and i == 0:
                    logger.debug(
                        'POST /deployments at 1st attempt failed, will retry in 2s...'
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
                        api_url = DEPLOYMENTS_API + "/" + self.deployment_id
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

                            if self.deployment_id is not json_response['id']:
                                # TODO: is this validation needed?
                                pass

                            logger.info(
                                f'Successfully submitted deployment with ID [bold][blue]{self.deployment_id}[/blue][/bold] to get updated'
                            )
                            return json_response
                except aiohttp.ClientConnectionError as e:
                    if i == 0:
                        logger.debug(
                            f'PUT /deployments/{self.deployment_id} at 1st attempt failed, will retry in 2s...'
                        )
                        await asyncio.sleep(2)
                    else:
                        logger.debug(
                            f'PUT /deployments/{self.deployment_id} retry failed too...'
                        )
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
            logger.info(
                f'Check the Deployment deployment logs: {await self.jcloud_logs} !'
            )
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
                                f'Successfully submitted deployment with ID [bold][blue]{self.deployment_id}[/blue][/bold]'
                            )
                            return json_response
                except aiohttp.ClientConnectionError as e:
                    if i == 0:
                        logger.debug(
                            f'PUT /deployments/{self.deployment_id} at 1st attempt failed, will retry in 2s...'
                        )
                        await asyncio.sleep(2)
                    else:
                        logger.debug(
                            f'PUT /deployments/{self.deployment_id} retry failed too...'
                        )
                        raise e

        with pbar:
            desired_phase = Phase.Serving
            intermediate_phases = [
                Phase.Empty,
                Phase.Pending,
                Phase.Updating,
                Phase.Starting,
            ]
            if cust_act is CustomAction.Restart:
                title = 'Restarting the Deployment'
                api_url = (
                    DEPLOYMENTS_API
                    + "/"
                    + self.deployment_id
                    + ":"
                    + CustomAction.Restart
                )
            elif cust_act == CustomAction.Pause:
                desired_phase = Phase.Paused
                title = 'Pausing the Deployment'
                api_url = (
                    DEPLOYMENTS_API
                    + "/"
                    + self.deployment_id
                    + ":"
                    + CustomAction.Pause
                )
                intermediate_phases.append(Phase.Serving)
            elif cust_act == CustomAction.Resume:
                title = 'Resuming the Deployment'
                api_url = (
                    DEPLOYMENTS_API
                    + "/"
                    + self.deployment_id
                    + ":"
                    + CustomAction.Resume
                )
                intermediate_phases.append(Phase.Paused)
            elif cust_act == CustomAction.Scale:
                title = 'Scaling Executor in Deployment'
                api_url = (
                    DEPLOYMENTS_API
                    + '/'
                    + self.deployment_id
                    + ':'
                    + CustomAction.Scale
                    + f'?replicas={kwargs["replicas"]}'
                )
            elif cust_act == CustomAction.Recreate:
                desired_phase = Phase.Serving
                title = 'Recreating the deleted Deployment'
                api_url = (
                    DEPLOYMENTS_API
                    + '/'
                    + self.deployment_id
                    + ':'
                    + CustomAction.Recreate
                )

            pbar.start_task(pb_task)
            pbar.update(
                pb_task,
                advance=1,
                description='Submitting',
                title=title,
            )
            await _custom_action(api_url=api_url)
            logger.info(
                f'Check the Deployment deployment logs: {await self.jcloud_logs} !'
            )
            self.endpoints, self.dashboard = await self._fetch_until(
                intermediate=intermediate_phases,
                desired=desired_phase,
            )
            if 'JCLOUD_HIDE_SUCCESS_MSG' not in os.environ:
                pbar.console.print(self)
            pbar.update(pb_task, description='Finishing', advance=1)

    async def restart(self):
        await self.custom_action(CustomAction.Restart)

    async def pause(self):
        self.deployment_status = "paused"
        await self.custom_action(CustomAction.Pause)

    async def resume(self):
        self.deployment_status = "available"
        await self.custom_action(CustomAction.Resume)

    async def scale(self, replicas):
        await self.custom_action(CustomAction.Scale, replicas=replicas)

    async def recreate(self):
        await self.custom_action(CustomAction.Recreate)

    @property
    async def jcloud_logs(self) -> str:
        return DASHBOARD_DEPLOYMENT_URL_LINK.format(deployment_id=self.deployment_id)

    @property
    async def status(self) -> Dict:
        async with get_aiohttp_session() as session:
            async with session.get(
                url=f'{DEPLOYMENTS_API}/{self.deployment_id}', headers=self.auth_header
            ) as response:
                json_response = await response.json()
                _exit_if_response_error(
                    response,
                    expected_status=HTTPStatus.OK,
                    json_response=json_response,
                )
                return await response.json()

    async def logs(self) -> Dict:
        _url = f'{DEPLOYMENTS_API}/{self.deployment_id}'
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

    async def list_all(
        self,
        phase: Optional[str] = None,
        name: Optional[str] = None,
        labels: Dict[str, str] = None,
    ) -> Dict:
        async with get_aiohttp_session() as session:
            _args = dict(url=DEPLOYMENTS_API, headers=self.auth_header)
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
                        f'\nYou don\'t have any Deployments deployed with status [green]{phase}[/green]. '
                        f'Please pass a different [i]--status[/i] or use [i]jc deploy[/i] to deploy a new Deployment'
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
                    DASHBOARD_DEPLOYMENT_URL_MARKDOWN.format(
                        deployment_id=self.deployment_id
                    ),
                )
            elif _current_phase not in intermediate:
                exit_error(
                    f'Unexpected phase: {_current_phase} reached at [b]{_last_phase}[/b] '
                    f'for Deployment ID [b]{self.deployment_id}[/b]'
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
                url=f'{DEPLOYMENTS_API}/{self.deployment_id}',
                headers=self.auth_header,
            ) as response:
                try:
                    json_response = await response.json()
                except json.decoder.JSONDecodeError:
                    exit_error(
                        f'Can\'t find [b]{self.deployment_id}[/b], check the ID or the deployment may be removed already.'
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
            logger.info(
                f'Check the Deployment deployment logs: {await self.jcloud_logs} !'
            )
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
                title=f'Removing deployment {self.deployment_id}',
            )
            await self._terminate()
            await self._fetch_until(
                intermediate=[Phase.Serving],
                desired=Phase.Deleted,
            )
            pbar.update(pb_task, description='Finishing', advance=1)
            await CloudDeployment._cancel_pending()

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
        my_table.add_row('ID', self.deployment_id)
        if self.endpoints:
            for k, v in self.endpoints.items():
                my_table.add_row(k.title(), v)
        if self.dashboard is not None:
            my_table.add_row('Dashboard', Markdown(self.dashboard))
        yield Panel(
            my_table,
            title=f':tada: Deployment is {self.deployment_status}!',
            expand=False,
            width=100,
        )


async def _terminate_deployment_simplified(
    deployment_id: str, phase: Optional[str] = None
):
    """Terminate a Deployment given deployment_id.

    This is a simplified version of CloudDeployment.__aexit__, i.e.,
    without reporting the details of the termination process using the progress bar.
    It's supposed to be used in the multi-deployment removal context.
    """

    deployment = CloudDeployment(deployment_id=deployment_id)
    await deployment._terminate()
    _intermediate_phases = [Phase.Serving]
    if phase is not None:
        _intermediate_phases.append(phase)
    await deployment._fetch_until(
        intermediate=_intermediate_phases,
        desired=Phase.Deleted,
    )

    # This needs to be returned so in asyncio.as_completed, it can be printed.
    return deployment_id
