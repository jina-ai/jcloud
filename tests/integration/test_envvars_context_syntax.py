import os
from typing import Dict

from jcloud.flow import CloudFlow
from jina import Client, DocumentArray

cur_dir = os.path.dirname(os.path.abspath(__file__))


def sorted_dict(d: Dict):
    return dict(sorted(d.items()))


def test_envvars_context_syntax():
    with CloudFlow(
        path=os.path.join(cur_dir, 'projects', 'envvars_context_syntax'),
        name='context-syntax',
    ) as flow:
        da = Client(host=flow.gateway).post(on='/', inputs=DocumentArray.empty(2))
        for d in da:
            assert sorted_dict(d.tags) == sorted_dict({'var_a': 56.0, 'var_b': 'abcd'})
