import os

import asyncio
import pytest

from jcloud.api import _remove_multi
from jcloud.constants import Status
from jcloud.flow import CloudFlow
from jcloud.helper import get_logger


logger = get_logger("Test Logger")

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
FLOW_FILE_PATH = os.path.join(flows_dir, f'http-stateless.yml')


async def _simplified_deploy(flow):
    """Simified deployment routinue without using progress bar just for testing purpose.

    Since progress bar doesn't support displaying many at once if flows are running concurrently,
    so we have to use this workaround.
    """

    json_result = await flow._deploy()
    flow.gateway = await flow._fetch_until(
        intermediate=[
            Status.SUBMITTED,
            Status.NORMALIZING,
            Status.NORMALIZED,
            Status.STARTING,
        ],
        desired=Status.ALIVE,
    )
    flow._c_logstream_task.cancel()
    return json_result['id']


@pytest.mark.asyncio
async def test_remove_selected_flows():
    initial_owned_flows_raw = await CloudFlow().list_all(status=Status.ALIVE.value)
    initial_owned_flows = {flow['id'] for flow in initial_owned_flows_raw}

    logger.info(f'Initial owned flows: {len(initial_owned_flows)}')
    flow_1 = _simplified_deploy(CloudFlow(path=FLOW_FILE_PATH, name='flow-1'))
    flow_2 = _simplified_deploy(CloudFlow(path=FLOW_FILE_PATH, name='flow-2'))

    logger.info(f'Deploying two new flows...')
    added_flows = set()
    for coro in asyncio.as_completed([flow_1, flow_2]):
        r = await coro
        added_flows.add(r)

    owned_flows_after_add_raw = await CloudFlow().list_all(status=Status.ALIVE.value)
    owned_flows_after_add = {flow['id'] for flow in owned_flows_after_add_raw}
    logger.info(f'New Flow added: {added_flows}')
    logger.info(f'Owned flows after new deployments: {len(owned_flows_after_add)}')
    assert len(initial_owned_flows) + 2 == len(owned_flows_after_add)
    assert added_flows.issubset(owned_flows_after_add)

    logger.info(f'Removing two new flows...')
    await _remove_multi(list(added_flows))

    owned_flows_after_delete_raw = await CloudFlow().list_all(status=Status.ALIVE.value)
    owned_flows_after_delete = {flow['id'] for flow in owned_flows_after_delete_raw}
    logger.info(f'Owned flows after removal: {len(owned_flows_after_delete)}')

    assert len(initial_owned_flows) == len(owned_flows_after_delete)
    assert (
        any([flow_id in owned_flows_after_delete for flow_id in added_flows]) == False
    )
