import os

import pytest
from jina import Client, DocumentArray

from jcloud.flow import CloudFlow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_project_multi_executors():
    with CloudFlow(path=os.path.join(cur_dir, 'projects', 'multi_executors')) as flow:
        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']

        da: DocumentArray = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray.empty(2),
        )
        for d in da:
            assert d.tags['MyExecutor1'] == 'init_var_ex1'
            assert d.tags['MyExecutor2'] == 'init_var_ex2'
