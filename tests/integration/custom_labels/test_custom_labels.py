import os

import pytest
from jina import Client, Document, DocumentArray

from jcloud.flow import CloudFlow

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
protocol = 'grpc'


def test_custom_labels():
    labels_file = 'valid-labels.yml'
    with CloudFlow(path=os.path.join(flows_dir, labels_file)) as flow:
        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50

        # TODO: check that the labels are actually set by searching for them
