import os

import pytest

from jina import Client, Document, DocumentArray

from jcloud.flow import CloudFlow

from jcloud.helper import get_dict_list_key_path
from tests.utils.utils import get_condition_from_status

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'base_flow.yml'
protocol = 'http'


def test_pause_resume_flow():
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

        # pause the flow
        flow._loop.run_until_complete(flow.pause())

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        status = flow._loop.run_until_complete(flow.status)
        cnd = get_condition_from_status(status)
        assert cnd is not None

        nltt = cnd["lastTransitionTime"]
        assert ltt < nltt

        assert get_dict_list_key_path(status, ["status", "phase"]) == "Paused"

        with pytest.raises(ValueError):
            da = Client(host=gateway).post(
                on='/',
                inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
            )

        # resume the flow
        ltt = nltt
        flow._loop.run_until_complete(flow.resume())

        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        status = flow._loop.run_until_complete(flow.status)
        cnd = get_condition_from_status(status)
        assert cnd is not None

        nltt = cnd["lastTransitionTime"]
        assert ltt < nltt

        assert get_dict_list_key_path(status, ["status", "phase"]) == "Serving"

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50
