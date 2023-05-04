import os

from jina import Client, Document, DocumentArray

from jcloud.flow import CloudFlow

from jcloud.helper import get_dict_list_key_path

cur_dir = os.path.dirname(os.path.abspath(__file__))
flow_file = 'flow.yml'
protocol = 'grpc'


def test_update_executor_args():
    os.environ["TEST"] = "test"
    with CloudFlow(path=os.path.join(cur_dir, flow_file)) as flow:

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        status = flow._loop.run_until_complete(flow.status)
        assert (
            get_dict_list_key_path(status, ['spec', 'executors', 0, 'env', 'TEST'])
            == 'test'
        )

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50
