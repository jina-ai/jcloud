import asyncio
import os

import pytest

from argparse import Namespace
from unittest.mock import patch

from jcloud.api import remove
from jcloud.flow import CloudFlow
from jcloud.constants import Phase
from jcloud.helper import get_logger, get_or_reuse_loop

from tests.integration.remove_multiple.test_multi_flows_removal import (
    _simplified_deploy,
    get_serving_flows,
)

NUM_FLOWS_TO_DEPLOY = 4
NUM_FLOWS_TO_PAUSE = 2

logger = get_logger("Test Logger")

flows_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'basic', 'flows'
)
flow = 'http-flow.yml'


async def get_paused_flows():
    fl = await CloudFlow().list_all(phase=Phase.Paused.value)
    return {flow['id'] for flow in fl['flows']}


@patch('rich.prompt.Confirm.ask', return_value=True)
def test_remove_flows_by_phase(mock_ask):
    initial_owned_flows = asyncio.run(get_serving_flows())

    logger.info(f'Initial owned flows: {len(initial_owned_flows)}')
    flow_1 = asyncio.run(
        _simplified_deploy(CloudFlow(path=os.path.join(flows_dir, flow)))
    )
    flow_2 = asyncio.run(
        _simplified_deploy(CloudFlow(path=os.path.join(flows_dir, flow)))
    )
    added_flows = {flow_1, flow_2}
    logger.info(f'Deploying two new flows...')

    owned_flows_after_add = asyncio.run(get_serving_flows())
    logger.info(f'New Flow added: {added_flows}')
    logger.info(f'Owned flows after new deployments: {len(owned_flows_after_add)}')

    assert added_flows.issubset(owned_flows_after_add)

    for flow_id in added_flows:
        asyncio.run(CloudFlow(flow_id=flow_id).pause())

    logger.info(f'Removing two new flows by phase...')
    args = Namespace()
    args.phase = 'Paused'
    args.flows = []
    remove(args)
    paused_flows = asyncio.run(get_paused_flows())

    assert any([flow_id in paused_flows for flow_id in added_flows]) == False


@patch('rich.prompt.Confirm.ask', return_value=True)
def test_remove_flows_by_phase_and_list_with_empty_intersection(mock_ask):
    initial_owned_flows = asyncio.run(get_serving_flows())
    logger.info(f'Initial owned flows: {len(initial_owned_flows)}')
    added_flows = []

    for _ in range(NUM_FLOWS_TO_DEPLOY):
        added_flows.append(
            asyncio.run(
                _simplified_deploy(CloudFlow(path=os.path.join(flows_dir, flow)))
            )
        )
    logger.info(f'Deploying {NUM_FLOWS_TO_DEPLOY} new flows...')

    owned_flows_after_add = asyncio.run(get_serving_flows())

    logger.info(f'New Flow added: {added_flows}')
    logger.info(f'Owned flows after new deployments: {len(owned_flows_after_add)}')
    assert set(added_flows).issubset(owned_flows_after_add)

    for i in range(NUM_FLOWS_TO_PAUSE):
        asyncio.run(CloudFlow(flow_id=added_flows[i]).pause())

    logger.info(f'Removing new flows by phase and list...')

    args = Namespace()
    args.phase = 'Paused'
    args.flows = added_flows[NUM_FLOWS_TO_PAUSE:]
    remove(args)

    paused_flows = asyncio.run(get_paused_flows())
    owned_flows_after_add = asyncio.run(get_serving_flows())

    assert any([flow_id in owned_flows_after_add for flow_id in added_flows]) == False
    assert any([flow_id in paused_flows for flow_id in added_flows]) == False


@patch('rich.prompt.Confirm.ask', return_value=True)
def test_remove_flows_by_phase_and_list_with_non_empty_intersection(mock_ask):
    initial_owned_flows = asyncio.run(get_serving_flows())
    logger.info(f'Initial owned flows: {len(initial_owned_flows)}')
    added_flows = []

    for _ in range(NUM_FLOWS_TO_DEPLOY):
        added_flows.append(
            asyncio.run(
                _simplified_deploy(CloudFlow(path=os.path.join(flows_dir, flow)))
            )
        )

    logger.info(f'Deploying {NUM_FLOWS_TO_DEPLOY} new flows...')
    owned_flows_after_add = asyncio.run(get_serving_flows())

    logger.info(f'New Flow added: {added_flows}')
    logger.info(f'Owned flows after new deployments: {len(owned_flows_after_add)}')

    assert set(added_flows).issubset(owned_flows_after_add)

    for i in range(NUM_FLOWS_TO_PAUSE):
        asyncio.run(CloudFlow(flow_id=added_flows[i]).pause())

    logger.info(f'Removing new flows by phase and list...')

    args = Namespace()
    args.phase = 'Paused'
    args.flows = added_flows[NUM_FLOWS_TO_PAUSE - 1 :]
    remove(args)

    paused_flows = asyncio.run(get_paused_flows())
    owned_flows_after_add = asyncio.run(get_serving_flows())

    assert any([flow_id in owned_flows_after_add for flow_id in added_flows]) == False
    assert any([flow_id in paused_flows for flow_id in added_flows]) == False
