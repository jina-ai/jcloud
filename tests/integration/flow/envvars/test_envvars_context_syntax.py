import os
from typing import Dict

import pytest
from jina import Client, DocumentArray

from jcloud.flow import CloudFlow

projects_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'projects'
)
protocol = 'grpc'


def sorted_dict(d: Dict):
    return dict(sorted(d.items()))


def test_envvars_context_syntax():
    with CloudFlow(
        path=os.path.join(projects_dir, 'envvars_context_syntax'),
    ) as flow:
        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')

        da = Client(host=gateway).post(on='/', inputs=DocumentArray.empty(2))
        for d in da:
            assert sorted_dict(d.tags) == sorted_dict({'var_a': 56.0, 'var_b': 'abcd'})
