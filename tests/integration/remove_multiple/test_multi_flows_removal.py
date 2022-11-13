import asyncio
import os

import pytest

from jcloud.api import _remove_multi
from jcloud.constants import Phase
from jcloud.flow import CloudFlow
from jcloud.helper import get_logger

logger = get_logger("Test Logger")

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_one = 'flow1.yml'
flow_two = 'flow2.yml'


async def _simplified_deploy(flow: CloudFlow):
    """Simplified deployment coroutine without using progress bar just for testing purpose.

    Since progress bar doesn't support displaying many at once if flows are running concurrently,
    so we have to use this workaround.
    """

    json_result = await flow._deploy()
    flow.endpoints, flow.dashboard = await flow._fetch_until(
        intermediate=[
            Phase.Empty,
            Phase.Pending,
            Phase.Starting,
        ],
        desired=Phase.Serving,
    )
    return json_result['id']


async def get_serving_flows():
    fl = await CloudFlow().list_all(phase=Phase.Serving.value)
    return {flow['id'] for flow in fl['flows']}


@pytest.mark.asyncio
async def test_remove_selected_flows():
    initial_owned_flows = await get_serving_flows()

    logger.info(f'Initial owned flows: {len(initial_owned_flows)}')
    flow_1 = _simplified_deploy(CloudFlow(path=os.path.join(flows_dir, flow_one)))
    flow_2 = _simplified_deploy(CloudFlow(path=os.path.join(flows_dir, flow_two)))

    logger.info(f'Deploying two new flows...')
    added_flows = set()
    for coro in asyncio.as_completed([flow_1, flow_2]):
        r = await coro
        added_flows.add(r)

    owned_flows_after_add = await get_serving_flows()
    logger.info(f'New Flow added: {added_flows}')
    logger.info(f'Owned flows after new deployments: {len(owned_flows_after_add)}')
    # assert len(initial_owned_flows) + 2 == len(owned_flows_after_add)
    assert added_flows.issubset(owned_flows_after_add)

    logger.info(f'Removing two new flows...')
    await _remove_multi(list(added_flows))

    owned_flows_after_delete = await get_serving_flows()
    logger.info(f'Owned flows after removal: {len(owned_flows_after_delete)}')

    # assert len(initial_owned_flows) == len(owned_flows_after_delete)
    assert (
        any([flow_id in owned_flows_after_delete for flow_id in added_flows]) == False
    )
