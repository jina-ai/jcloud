import os

import pytest
from jcloud.flow import CloudFlow
from jina import Client, DocumentArray

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.skip('non-interactive login not supported yet')
def test_project2():
    with CloudFlow(
        path=os.path.join(cur_dir, 'projects', 'testproject2'),
        name='testproject2',
    ) as flow:
        da: DocumentArray = Client(host=flow.gateway).post(
            on='/',
            inputs=DocumentArray.empty(2),
        )
        for d in da:
            assert d.tags['MyExecutor1'] == 'init_var_ex1'
            assert d.tags['MyExecutor2'] == 'init_var_ex2'
