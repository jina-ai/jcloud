import os

from jcloud.flow import CloudFlow
from jcloud.constants import Phase

from jcloud.helper import get_dict_list_key_path

from tests.utils import utils
from .. import FlowAlive

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'base_flow.yml'
resources_flow_file = 'update_resources.yml'
protocol = 'http'


def test_update_executor_resources():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:
        assert utils.eventually_reaches_phase(flow, Phase.Serving)

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        ltt = utils.get_last_transition_time(flow, FlowAlive)
        assert ltt

        assert utils.eventually_serve_requests(gateway)

        flow.path = os.path.join(flows_dir, resources_flow_file)
        flow._loop.run_until_complete(flow.update())
        assert utils.eventually_reaches_phase(flow, Phase.Serving)
        assert utils.eventually_condition_gets_updated(flow, FlowAlive, ltt)

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        status = flow._loop.run_until_complete(flow.status)

        res = get_dict_list_key_path(
            status, ['spec', 'executors', 0, 'jcloud', 'resources']
        )
        assert res is not None
        assert 'cpu' in res and res['cpu'] == '0.2'
        assert 'memory' in res and res['memory'] == '200M'

        assert utils.eventually_serve_requests(gateway)
