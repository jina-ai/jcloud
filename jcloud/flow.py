import asyncio
from contextlib import suppress
from dataclasses import dataclass
from enum import Enum
from http import HTTPStatus
from typing import Dict, List, Optional

import aiohttp

from . import WOLF_API, LOGSTREAM_API, AUTH_HEADERS
from .helper import get_or_reuse_loop, get_logger

logger = get_logger()


class Status(str, Enum):
    SUBMITTED = 'SUBMITTED'
    STARTING = 'STARTING'
    FAILED = 'FAILED'
    ALIVE = 'ALIVE'
    UPDATING = 'UPDATING'
    DELETING = 'DELETING'
    DELETED = 'DELETED'

    def streamable(self) -> bool:
        return self in (Status.ALIVE, Status.UPDATING, Status.DELETING)

    def alive(self) -> bool:
        return self == Status.ALIVE

    def deleted(self) -> bool:
        return self == Status.DELETED


@dataclass
class WolfFlow:
    filepath: Optional[str] = None
    name: Optional[str] = None
    workspace: Optional[str] = None
    flow_id: Optional[str] = None
    enable_logstream: bool = False

    @property
    def host(self) -> str:
        return f'{self.name}-{self.flow_id.split("-")[1]}.wolf.jina.ai'

    @property
    def loop(self):
        return get_or_reuse_loop()

    async def deploy(self):
        with open(self.filepath) as f:
            params = {}
            if self.name:
                params['name'] = self.name
            if self.workspace:
                params['workspace'] = self.workspace

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url=WOLF_API,
                        data={'yaml': f},
                        params=params,
                        headers=AUTH_HEADERS,
                ) as response:
                    json_response = await response.json()
                    assert (
                            response.status == HTTPStatus.CREATED
                    ), f'Got Invalid response status {response.status}, expected {HTTPStatus.CREATED}'
                    if self.name is not None:
                        assert self.name in json_response['name']
                    assert Status(json_response['status']) == Status.SUBMITTED
                    self.flow_id: str = json_response['id']
                    self.workspace: str = json_response['workspace']
                    self._c_logstream_task = asyncio.create_task(
                        WolfFlow.logstream({'request_id': json_response['request_id']})
                    )
                    logger.info(
                        f'POST /flows with flow_id {self.flow_id} & '
                        f'request_id {json_response["request_id"]}'
                    )
                    return json_response

    @staticmethod
    async def fetch(flow_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=f'{WOLF_API}/{flow_id}') as response:
                response.raise_for_status()
                return await response.json()

    async def fetch_until(
            self,
            intermediate: List[Status],
            desired: Status = Status.ALIVE,
    ):
        count = 0
        while count < 100:
            json_response = await WolfFlow.fetch(self.flow_id)
            if Status(json_response['status']) == desired:
                gateway = json_response["gateway"]
                logger.info(
                    f'Successfully reached status: {desired} with gateway {gateway}'
                )
                return gateway
            else:
                current_status = Status(json_response['status'])
                assert current_status in intermediate
                logger.debug(
                    f'current status is {current_status}, sleeping for 10secs'
                )
                await asyncio.sleep(10)
                count += 1

    async def terminate(self):
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                    url=f'{WOLF_API}/{self.flow_id}',
                    headers=AUTH_HEADERS,
            ) as response:
                json_response = await response.json()
                assert (
                        response.status == HTTPStatus.ACCEPTED
                ), f'Got Invalid response status {response.status}, expected {HTTPStatus.ACCEPTED}'
                self.t_logstream_task = asyncio.create_task(
                    WolfFlow.logstream(
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
                        logger.info(
                            f'Successfully connected to logstream API with params: {params}'
                        )
                        await ws.send_json({})
                        async for msg in ws:
                            if msg.type == aiohttp.http.WSMsgType.TEXT:
                                log_dict: Dict = msg.json()
                                if log_dict.get('status') == 'STREAMING':
                                    print(log_dict['message'])
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
        await self.deploy()
        self.gateway = await self.fetch_until(
            intermediate=[Status.SUBMITTED, Status.STARTING],
            desired=Status.ALIVE,
        )
        await self._c_logstream_task
        if self.enable_logstream:
            self.logstream_task = self.loop.create_task(
                WolfFlow.logstream(params={'flow_id': str(self.flow_id)})
            )
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.terminate()
        await self.fetch_until(
            intermediate=[Status.DELETING],
            desired=Status.DELETED,
        )
        await self.t_logstream_task
        await WolfFlow.cancel_pending()

    @staticmethod
    async def cancel_pending():
        for task in asyncio.all_tasks():
            task.cancel()
            with suppress(asyncio.CancelledError, RuntimeError):
                await task

    def __enter__(self):
        return self.loop.run_until_complete(self.__aenter__())

    def __exit__(self, *args, **kwargs):
        self.loop.run_until_complete(self.__aexit__(*args, **kwargs))
