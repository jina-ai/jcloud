import os

import pytest
from jina import Client, Document, DocumentArray

from jcloud.flow import CloudFlow

cur_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flow')
flow_file = 'flow.yml'


def test_executor_with_no_uses():
    with CloudFlow(path=os.path.join(cur_dir, flow_file)) as flow:
        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50
