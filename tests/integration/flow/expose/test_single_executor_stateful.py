import os

import numpy as np
from jina import Document, Flow

from jcloud.flow import CloudFlow
from jcloud.helper import remove_prefix

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'single-executor-stateful.yml'


def test_single_executor_stateful():
    index_docs = [
        Document(text=f'text-{i}', embedding=np.array([i, i + 1, i + 2]))
        for i in range(5)
    ]
    query_doc = index_docs[0]

    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:
        assert flow.endpoints != {}
        assert 'simpleindexer' in flow.endpoints
        simpleindexer_host = flow.endpoints['simpleindexer']
        with Flow().add(
            host=remove_prefix(simpleindexer_host, 'grpcs://'),
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
