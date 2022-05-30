import os

import numpy as np
import pytest
from jcloud.flow import CloudFlow
from jina import Client, Document

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flows')


def test_crud_stateful_flow_http():
    # This tests
    # Index Flow stores data on disk -> terminated
    # Query Flow accesses same data using Index Flows workspace to `/search`
    protocol = 'websocket'
    INDEX_FLOW_NAME = f'simpleindexer-{protocol}-index'
    SEARCH_FLOW_NAME = F'simpleindexer-{protocol}-search'
    FLOW_FILE_PATH = os.path.join(flows_dir, f'{protocol}-stateful.yml')

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
        path=FLOW_FILE_PATH, name=SEARCH_FLOW_NAME, workspace_id=index_flow.workspace_id
    ) as search_flow:
        da_search = Client(host=search_flow.gateway).search(inputs=query_doc)
        assert da_search[0].matches.texts == [f'text-{i}' for i in range(5)]
        for limit in [3, 5]:
            da_search = Client(host=search_flow.gateway).search(
                inputs=query_doc, parameters={'limit': limit}
            )
            assert len(da_search[0].matches.texts) == limit
            assert da_search[0].matches.texts == [f'text-{i}' for i in range(limit)]
