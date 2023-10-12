import os

import pytest

from jina import Client, Document, DocumentArray

from jcloud.flow import CloudFlow
from jcloud.constants import Phase

from tests.utils import utils
from .. import FlowAlive

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'base_flow.yml'
protocol = 'http'


def test_pause_resume_flow():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:
        assert utils.eventually_reaches_phase(flow, Phase.Serving)

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        ltt = utils.get_last_transition_time(flow, FlowAlive)
        assert ltt

        assert utils.eventually_serve_requests(gateway)

        # pause the flow
        flow._loop.run_until_complete(flow.pause())
        assert utils.eventually_reaches_phase(flow, Phase.Paused)
        assert utils.eventually_condition_gets_updated(flow, FlowAlive, ltt)

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        with pytest.raises(ValueError):
            da = Client(host=gateway).post(
                on='/',
                inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
            )

        # resume the flow
        ltt = utils.get_last_transition_time(flow, FlowAlive)
        assert ltt

        flow._loop.run_until_complete(flow.resume())
        assert utils.eventually_reaches_phase(flow, Phase.Serving)
        assert utils.eventually_condition_gets_updated(flow, FlowAlive, ltt)

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        assert utils.eventually_serve_requests(gateway)
