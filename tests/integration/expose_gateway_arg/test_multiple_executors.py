import os

from jcloud.flow import CloudFlow
from jcloud.helper import remove_prefix
from jina import Document, DocumentArray, Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_multiple_executors():
    with CloudFlow(
        path=os.path.join(cur_dir, 'flows', 'multiple-executors.yml'),
        name='multiple-execs',
    ) as flow:
        assert 'sentencizer' in flow.endpoints
        _sentencizer_host = flow.endpoints['sentencizer']
        assert 'simpleindexer' in flow.endpoints
        _simpleindexer_host = flow.endpoints['simpleindexer']

        with Flow().add(
            host=remove_prefix(_sentencizer_host, 'grpcs://'),
            external=True,
            port=443,
            tls=True,
        ).add(
            host=remove_prefix(_simpleindexer_host, 'grpcs://'),
            external=True,
            port=443,
            tls=True,
        ) as f:
            da = f.post(
                on='/',
                inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
            )
            assert len(da.texts) == 50
