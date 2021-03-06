import os

from jcloud.flow import CloudFlow
from jina import Client, DocumentArray

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_project_multi_executors():
    with CloudFlow(
        path=os.path.join(cur_dir, 'projects', 'multi_executors'),
        name='multi_executors',
    ) as flow:
        da: DocumentArray = Client(host=flow.gateway).post(
            on='/',
            inputs=DocumentArray.empty(2),
        )
        for d in da:
            assert d.tags['MyExecutor1'] == 'init_var_ex1'
            assert d.tags['MyExecutor2'] == 'init_var_ex2'
