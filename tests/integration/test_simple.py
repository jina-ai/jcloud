import os

import pytest
from jina import Client, DocumentArray

from jcloud.flow import CloudFlow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_project_simple():
    with CloudFlow(
        path=os.path.join(cur_dir, 'projects', 'simple')
    ) as flow:
        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray.empty(2),
        )
        assert da.texts == ['hello, world!', 'goodbye, world!']
