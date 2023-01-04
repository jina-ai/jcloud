import os

from jina import Client, Document, DocumentArray, Flow

from jcloud.flow import CloudFlow

from jcloud.helper import get_dict_list_key_path, get_condition_from_status

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'base_flow.yml'
protocol = 'http'


def test_restart_flow():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        status = flow._loop.run_until_complete(flow.status)
        cnd = get_condition_from_status(status)
        assert cnd is not None
        ltt = cnd["lastTransitionTime"]

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50

        # restart the flow
        flow._loop.run_until_complete(flow.restart())

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        status = flow._loop.run_until_complete(flow.status)
        cnd = get_condition_from_status(status)
        assert cnd is not None

        nltt = cnd["lastTransitionTime"]
        assert ltt < nltt

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50

        # restart the gateway of the flow
        ltt = nltt
        flow._loop.run_until_complete(flow.restart(gateway=True))

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        status = flow._loop.run_until_complete(flow.status)
        cnd = get_condition_from_status(status)
        assert cnd is not None

        nltt = cnd["lastTransitionTime"]
        assert ltt < nltt

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50

        # restart one of the executors of the flow
        ltt = nltt
        flow._loop.run_until_complete(flow.restart(executor='executor0'))

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        status = flow._loop.run_until_complete(flow.status)
        cnd = get_condition_from_status(status)
        assert cnd is not None

        nltt = cnd["lastTransitionTime"]
        assert ltt < nltt

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50
