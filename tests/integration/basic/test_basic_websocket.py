import os

from jina import Client, Document, DocumentArray

from jcloud.flow import CloudFlow

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'websocket-flow.yml'
protocol = 'ws'


def test_basic_websocket_flow():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:
        assert flow.endpoints != {}
        assert flow.endpoints['gateway'].startswith(f'{protocol}s://')
        gateway = flow.endpoints['gateway']

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50
