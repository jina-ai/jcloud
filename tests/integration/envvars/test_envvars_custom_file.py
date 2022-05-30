import os

import pytest
from jcloud.flow import CloudFlow
from jina import Client, DocumentArray

projects_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'projects'
)


def sorted_dict(d):
    return dict(sorted(d.items()))


def test_envvars_custom_file():
    with CloudFlow(
        path=os.path.join(projects_dir, 'envvars_custom_file'),
        name='custom-env',
        env_file=os.path.join(projects_dir, 'envvars_custom_file', 'custom.env'),
    ) as flow:
        da = Client(host=flow.gateway).post(on='/', inputs=DocumentArray.empty(2))
        for d in da:
            assert sorted_dict(d.tags) == sorted_dict({'var_a': 56.0, 'var_b': 'abcd'})


def test_envvars_custom_file_non_existing():
    with pytest.raises(SystemExit):
        with CloudFlow(
            path=os.path.join(projects_dir, 'envvars_custom_file'),
            name='custom-env',
            env_file=os.path.join(
                projects_dir, 'envvars_custom_file', 'non-existing.env'
            ),
        ):
            pass
