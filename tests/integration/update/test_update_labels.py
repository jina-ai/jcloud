import os

from jina import Client, Document, DocumentArray

from jcloud.flow import CloudFlow

from jcloud.helper import get_dict_list_key_path

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'base_flow.yml'
add_labels_flow_file = 'add_labels.yml'
modify_delete_labels_flow_file = "modify_delete_labels.yml"
protocol = 'http'

def test_update_labels_of_flow():
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

        flow.path = os.path.join(flows_dir, add_labels_flow_file)
        flow._loop.run_until_complete(flow.update())

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        status = flow._loop.run_until_complete(flow.status)

        labels = get_dict_list_key_path(status, ['spec', 'jcloud', 'labels'])
        assert "jina.ai/username" in labels and  labels["jina.ai/username"] == "johndoe"
        assert "jina.ai/application" in labels and  labels["jina.ai/application"] == "fashion-search"

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50
        
        flow.path = os.path.join(flows_dir, modify_delete_labels_flow_file)
        flow._loop.run_until_complete(flow.update())

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        status = flow._loop.run_until_complete(flow.status)

        labels = get_dict_list_key_path(status, ['spec', 'jcloud', 'labels'])
        assert "jina.ai/username" not in labels
        assert "jina.ai/application" in labels and  labels["jina.ai/application"] == "retail-search"

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50
