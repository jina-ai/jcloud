import os

from jcloud.flow import CloudFlow
from jcloud.constants import Phase

from tests.utils import utils
from .. import FlowAlive

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'base_flow.yml'
protocol = 'http'


def test_recreate_flow():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:
        assert utils.eventually_reaches_phase(flow, Phase.Serving)

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        ltt = utils.get_last_transition_time(flow, FlowAlive)
        assert ltt

        assert utils.eventually_serve_requests(gateway)

        # terminate the flow
        flow._loop.run_until_complete(flow._terminate())
        assert utils.eventually_reaches_phase(flow, Phase.Deleted)

        # recreate the flow
        flow._loop.run_until_complete(flow.recreate())
        assert utils.eventually_reaches_phase(flow, Phase.Serving)
        assert utils.eventually_condition_gets_updated(flow, FlowAlive, ltt)

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        assert utils.eventually_serve_requests(gateway)
