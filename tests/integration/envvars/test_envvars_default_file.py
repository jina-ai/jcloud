import os

import pytest
from jina import Client, DocumentArray

from jcloud.flow import CloudFlow
from jcloud.env_helper import EnvironmentVariables
from jcloud.normalize_helper import load_envs

projects_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'projects'
)
protocol = 'grpc'

def sorted_dict(d):
    return dict(sorted(d.items()))


def test_envvars_default_file():
    with CloudFlow(path=os.path.join(projects_dir, 'envvars_default_file')) as flow:
        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')
        envs = load_envs(os.path.join(projects_dir, 'envvars_default_file', '.env'))
        with EnvironmentVariables(envs) as _:
            da = Client(host=gateway).post(on='/', inputs=DocumentArray.empty(2))
            for d in da:
                assert sorted_dict(d.tags) == sorted_dict({'var_a': 56.0, 'var_b': 'abcd'})
