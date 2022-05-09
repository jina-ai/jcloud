import os

import pytest
from jcloud.flow import CloudFlow
from jina import Client, DocumentArray

cur_dir = os.path.dirname(os.path.abspath(__file__))


def sorted_dict(d):
    return dict(sorted(d.items()))


@pytest.mark.skip('non-interactive login not supported yet')
def test_envvars_default_file():
    with CloudFlow(
        path=os.path.join(cur_dir, 'projects', 'envvars_default_file'),
        name='default-env',
    ) as flow:
        da = Client(host=flow.gateway).post(on='/', inputs=DocumentArray.empty(2))
        for d in da:
            assert sorted_dict(d.tags) == sorted_dict({'var_a': 56.0, 'var_b': 'abcd'})
