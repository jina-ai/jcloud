import os

from jina import Client, Document, DocumentArray, Flow

from jcloud.flow import CloudFlow
from jcloud.helper import remove_prefix

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'gateway-and-executors.yml'


def test_multiple_executors():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:
        assert flow.endpoints != {}

        # Send data to the gateway
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50

        assert 'sentencizer' in flow.endpoints
        sentencizer_host = flow.endpoints['sentencizer']
        assert 'simpleindexer' in flow.endpoints
        simpleindexer_host = flow.endpoints['simpleindexer']

        # Test local gateway with remote executors
        with Flow().add(
            host=remove_prefix(sentencizer_host, 'grpcs://'),
            external=True,
            port=443,
            tls=True,
        ).add(
            host=remove_prefix(simpleindexer_host, 'grpcs://'),
            external=True,
            port=443,
            tls=True,
        ) as f:
            da = f.post(
                on='/',
                inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
            )
            assert len(da.texts) == 50
