import os

from jina import Client, Document, DocumentArray

from jcloud.flow import CloudFlow

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'valid-name.yml'
protocol = 'grpc'
custom_name = 'fashion-data'


def test_valid_custom_name():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:
        assert custom_name in flow.flow_id
        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')
        assert custom_name in gateway

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50
