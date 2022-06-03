import os

from jcloud.flow import CloudFlow
from jcloud.helper import remove_prefix
from jina import Document, DocumentArray, Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_single_executor_stateless():
    with CloudFlow(
        path=os.path.join(cur_dir, 'flows', 'single-executor-stateless.yml'),
        name='se-stateless',
    ) as flow:
        assert 'sentencizer' in flow.endpoints
        _host = flow.endpoints['sentencizer']
        with Flow().add(
            host=remove_prefix(_host, 'grpcs://'),
            external=True,
            port=443,
            tls=True,
        ) as f:
            da = f.post(
                on='/',
                inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
            )
            assert len(da.texts) == 50
