import os

import pytest
from jcloud.flow import CloudFlow
from jina import Client, Document, DocumentArray

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.skip('non-interactive login not supported yet')
@pytest.mark.parametrize('protocol', ['http', 'grpc'])
def test_crud_stateless_flow(protocol):
    with CloudFlow(
        path=os.path.join(cur_dir, 'flows', f'{protocol}-stateless.yml'),
        name=f'sentencizer-{protocol}',
    ) as flow:
        assert flow.gateway == f'{protocol}s://{flow.host}'
        da = Client(host=flow.gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50
