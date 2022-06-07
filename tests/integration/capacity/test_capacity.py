import os

from jcloud.flow import CloudFlow
from jina import Client, DocumentArray

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_capacity():
    with CloudFlow(
        path=os.path.join(cur_dir, 'flows', 'capacity.yml'),
        name='executor-capacity',
    ) as flow:
        da = Client(host=flow.gateway).post(on='/', inputs=DocumentArray.empty(50))
        assert len(da.texts) == 50
