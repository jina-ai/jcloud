import os

import pytest
from jcloud.flow import CloudFlow
from jina import Client, DocumentArray

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='non-interactive login not supported via GH Actions',
)
def test_project_simple():
    with CloudFlow(
        path=os.path.join(cur_dir, 'projects', 'testproject_simple'),
        name='testproject_simple',
    ) as flow:
        da = Client(host=flow.gateway).post(
            on='/',
            inputs=DocumentArray.empty(2),
        )
        assert da.texts == ['hello, world!', 'goodbye, world!']
