import os

import pytest
from jcloud.flow import CloudFlow
from jina import Client, DocumentArray

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.skip('non-interactive login not supported yet')
def test_project1():
    with CloudFlow(
        path=os.path.join(cur_dir, 'projects', 'testproject1'),
        name='testproject1',
    ) as flow:
        da = Client(host=flow.gateway).post(
            on='/',
            inputs=DocumentArray.empty(2),
        )
        assert da.texts == ['hello, world!', 'goodbye, world!']
