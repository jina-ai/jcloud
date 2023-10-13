import os

from jina import Document, DocumentArray, Flow

from jcloud.flow import CloudFlow
from jcloud.helper import remove_prefix

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'single-executor-stateless.yml'


def test_single_executor_stateless():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:
        assert flow.endpoints != {}
        assert 'sentencizer' in flow.endpoints
        sentencizer_host = flow.endpoints['sentencizer']
        with Flow().add(
            host=remove_prefix(sentencizer_host, 'grpcs://'),
            external=True,
            port=443,
            tls=True,
        ) as f:
            da = f.post(
                on='/',
                inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
            )
            assert len(da.texts) == 50
