import os

from jina import Client, Document, DocumentArray, Flow

from jcloud.flow import CloudFlow
from jcloud.helper import remove_prefix

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'base_flow.yml'
exposed_executor_flow_file = 'expose_executor.yml'
protocol = 'http'

def test_update_executor_expose():
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

        flow.path = os.path.join(flows_dir, exposed_executor_flow_file)
        flow._loop.run_until_complete(flow.update())
        import time; time.sleep(15)
        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        assert 'executor0' in flow.endpoints
        exc_host = flow.endpoints['executor0']

        import time; time.sleep(20)

        with Flow(protocol='HTTP').add(
            host=remove_prefix(exc_host, 'grpcs://'),
            external=True,
            port=443,
            tls=True,
        ) as f:
            da = f.post(
                on='/',
                inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
            )
            assert len(da.texts) == 50


def test_update_executor_unexpose():
    with CloudFlow(path=os.path.join(flows_dir, exposed_executor_flow_file)) as flow:

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')
        assert 'executor0' in flow.endpoints

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50

        flow.path = os.path.join(flows_dir, flow_file)
        flow._loop.run_until_complete(flow.update())

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        assert 'executor0' not in flow.endpoints

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50
