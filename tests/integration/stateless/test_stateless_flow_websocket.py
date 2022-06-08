import os

import pytest
from jcloud.flow import CloudFlow
from jina import Client, Document, DocumentArray

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flows')


def test_crud_stateless_flow_websocket():
    protocol = 'websocket'
    with CloudFlow(
        path=os.path.join(flows_dir, f'{protocol}-stateless.yml'),
        name=f'sentencizer-{protocol}',
    ) as flow:
        assert flow.gateway == f'wss://{flow.host}'
        da = Client(host=flow.gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50
