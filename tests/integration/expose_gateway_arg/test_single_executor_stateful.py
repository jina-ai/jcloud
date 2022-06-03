import os

import numpy as np
from jcloud.flow import CloudFlow
from jcloud.helper import remove_prefix
from jina import Document, DocumentArray, Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_single_executor_stateful():
    index_docs = [
        Document(text=f'text-{i}', embedding=np.array([i, i + 1, i + 2]))
        for i in range(5)
    ]
    query_doc = index_docs[0]

    with CloudFlow(
        path=os.path.join(cur_dir, 'flows', 'single-executor-stateful.yml'),
        name='se-stateful-first',
    ) as first:
        assert 'simpleindexer' in first.endpoints
        _host = first.endpoints['simpleindexer']
        with Flow().add(
            host=remove_prefix(_host, 'grpcs://'),
            external=True,
            port=443,
            tls=True,
        ) as f1:
            da_index = f1.index(inputs=index_docs)
            assert da_index.texts == [f'text-{i}' for i in range(5)]
            for limit in [3, 5]:
                da_search = f1.search(
                    inputs=query_doc,
                    parameters={'limit': limit},
                )
                assert len(da_search[0].matches.texts) == limit
                assert da_search[0].matches.texts == [f'text-{i}' for i in range(limit)]

    with CloudFlow(
        path=os.path.join(cur_dir, 'flows', 'single-executor-stateful.yml'),
        name='se-stateful-second',
        workspace_id=first.workspace_id,
    ) as second:
        assert 'simpleindexer' in second.endpoints
        _host = second.endpoints['simpleindexer']
        with Flow().add(
            host=remove_prefix(_host, 'grpcs://'),
            external=True,
            port=443,
            tls=True,
        ) as f2:
            da_search = f2.search(inputs=query_doc)
            assert da_search[0].matches.texts == [f'text-{i}' for i in range(5)]
            for limit in [3, 5]:
                da_search = f2.search(inputs=query_doc, parameters={'limit': limit})
                assert len(da_search[0].matches.texts) == limit
                assert da_search[0].matches.texts == [f'text-{i}' for i in range(limit)]
