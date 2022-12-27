import os

from jina import Client, Document, DocumentArray

from jcloud.flow import CloudFlow

from jcloud.helper import get_dict_list_key_path

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'base_flow.yml'
resources_flow_file = 'update_resources.yml'
protocol = 'http'

def test_update_executor_resources():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50

        flow.path = os.path.join(flows_dir, resources_flow_file)
        flow._loop.run_until_complete(flow.update())

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        status = flow._loop.run_until_complete(flow.status)

        res = get_dict_list_key_path(status, ['spec', 'executors', 0, 'jcloud', 'resources'])
        assert res is not None
        assert 'cpu' in res and res['cpu'] == '0.2'
        assert 'memory' in res and res['memory'] == '200M'

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50
