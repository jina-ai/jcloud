import os

from jcloud.flow import CloudFlow
from jcloud.constants import Phase

from jcloud.helper import get_dict_list_key_path

from tests.utils import utils
from .. import FlowAlive

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'base_flow.yml'
new_exc_args_flow_file = 'add_args.yml'
protocol = 'http'


def test_update_executor_args():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:
        assert utils.eventually_reaches_phase(flow, Phase.Serving)

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        ltt = utils.get_last_transition_time(flow, FlowAlive)
        assert ltt

        assert utils.eventually_serve_requests(gateway)

        flow.path = os.path.join(flows_dir, new_exc_args_flow_file)
        flow._loop.run_until_complete(flow.update())
        assert utils.eventually_reaches_phase(flow, Phase.Serving)
        assert utils.eventually_condition_gets_updated(flow, FlowAlive, ltt)

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        status = flow._loop.run_until_complete(flow.status)
        assert (
            get_dict_list_key_path(
                status, ['spec', 'executors', 0, 'uses_with', 'punct_chars']
            )
            == '$PUNCT_CHARS'
        )

        assert utils.eventually_serve_requests(gateway)
