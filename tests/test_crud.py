import os

import numpy as np
import pytest
from jcloud.flow import CloudFlow
from jina import Client, Document, DocumentArray

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize('protocol', ['http', 'grpc'])
def test_crud_stateless_flow(protocol):
    with CloudFlow(
        path=os.path.join(cur_dir, 'flows', f'flow-{protocol}-stateless.yml'),
        name=f'sentencizer-{protocol}',
    ) as flow:
        assert flow.gateway == f'{protocol}s://{flow.host}'
        da = Client(host=flow.gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50


@pytest.mark.parametrize('protocol', ['http', 'grpc'])
def test_crud_stateful_flow(protocol):
    # This tests
    # Index Flow stores data on disk -> terminated
    # Query Flow accesses same data using Index Flows workspace to `/search`
    INDEX_FLOW_NAME = f'simpleindexer-{protocol}-index'
    SEARCH_FLOW_NAME = F'simpleindexer-{protocol}-search'
    FLOW_FILE_PATH = os.path.join(cur_dir, 'flows', f'flow-{protocol}-stateful.yml')

    index_docs = [
        Document(text=f'text-{i}', embedding=np.array([i, i + 1, i + 2]))
        for i in range(5)
    ]
    query_doc = index_docs[0]

    with CloudFlow(path=FLOW_FILE_PATH, name=INDEX_FLOW_NAME) as index_flow:
        da_index = Client(host=index_flow.gateway).index(inputs=index_docs)
        assert da_index.texts == [f'text-{i}' for i in range(5)]
        for limit in [3, 5]:
            da_search = Client(host=index_flow.gateway).search(
                inputs=query_doc, parameters={'limit': limit}
            )
            assert len(da_search[0].matches.texts) == limit
            assert da_search[0].matches.texts == [f'text-{i}' for i in range(limit)]

    with CloudFlow(
        path=FLOW_FILE_PATH, name=SEARCH_FLOW_NAME, workspace=index_flow.workspace
    ) as search_flow:
        da_search = Client(host=search_flow.gateway).search(inputs=query_doc)
        assert da_search[0].matches.texts == [f'text-{i}' for i in range(5)]
        for limit in [3, 5]:
            da_search = Client(host=search_flow.gateway).search(
                inputs=query_doc, parameters={'limit': limit}
            )
            assert len(da_search[0].matches.texts) == limit
            assert da_search[0].matches.texts == [f'text-{i}' for i in range(limit)]
