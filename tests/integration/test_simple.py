import os

from jcloud.flow import CloudFlow
from jina import Client, DocumentArray

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_project_simple():
    with CloudFlow(
        path=os.path.join(cur_dir, 'projects', 'simple'),
        name='simple',
    ) as flow:
        da = Client(host=flow.gateway).post(
            on='/',
            inputs=DocumentArray.empty(2),
        )
        assert da.texts == ['hello, world!', 'goodbye, world!']
