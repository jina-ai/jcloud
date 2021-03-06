import os

import pytest
from jcloud.flow import CloudFlow

cur_dir = os.path.dirname(os.path.abspath(__file__))


async def func(*args, **kwargs):
    return 'b'


@pytest.mark.asyncio
@pytest.mark.parametrize('filename', ('grpc-stateful.yml', 'http-stateful.yml'))
async def test_post_params_normalized_flow(monkeypatch, filename):
    flow = CloudFlow(path=os.path.join(cur_dir, '..', 'integration', 'flows', filename))
    monkeypatch.setattr(flow, '_zip_and_upload', func)
    _post_params = await flow._get_post_params()
    assert 'data' in _post_params
    assert len(_post_params['data']._fields) == 1
    assert _post_params['data']._fields[0][0]['name'] == 'yaml'
    assert 'params' in _post_params
    assert _post_params['params'] == {}


@pytest.mark.asyncio
async def test_post_params_normalized_flow_with_env(monkeypatch):
    flow = CloudFlow(
        path=os.path.join(cur_dir, '..', 'integration', 'flows', 'with-envs.yml'),
        env_file=os.path.join(cur_dir, '..', 'integration', 'flows', 'sentencizer.env'),
    )
    monkeypatch.setattr(flow, '_zip_and_upload', func)
    _post_params = await flow._get_post_params()
    assert 'data' in _post_params
    assert len(_post_params['data']._fields) == 2
    assert _post_params['data']._fields[0][0]['name'] == 'yaml'
    assert _post_params['data']._fields[1][0]['name'] == 'envs'
    assert 'params' in _post_params
    assert _post_params['params'] == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'dirname',
    (
        'simple',
        'multi_executors',
        'envvars_custom_file',
        'envvars_default_file',
    ),
)
async def test_post_params_local_project_file(monkeypatch, dirname):
    flow = CloudFlow(
        path=os.path.join(cur_dir, '..', 'integration', 'projects', dirname, 'flow.yml')
    )
    monkeypatch.setattr(flow, '_zip_and_upload', func)
    _post_params = await flow._get_post_params()
    assert 'data' not in _post_params
    assert 'params' in _post_params
    assert 'artifactid' in _post_params['params']


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'dirname',
    (
        'simple',
        'multi_executors',
        'envvars_custom_file',
        'envvars_default_file',
    ),
)
async def test_post_params_local_project_dir(monkeypatch, dirname):
    flow = CloudFlow(
        path=os.path.join(cur_dir, '..', 'integration', 'projects', dirname)
    )
    monkeypatch.setattr(flow, '_zip_and_upload', func)
    _post_params = await flow._get_post_params()
    assert 'data' not in _post_params
    assert 'params' in _post_params
    assert 'artifactid' in _post_params['params']


def test_valid_env():
    flow = CloudFlow(
        path=os.path.join(cur_dir, '..', 'integration', 'flows', 'with-envs.yml'),
        env_file=os.path.join(cur_dir, '..', 'integration', 'flows', 'sentencizer.env'),
    )
    assert flow.envs == {'PUNCT_CHARS': '(!,)'}


@pytest.mark.parametrize(
    'parent_dir, path_name, env_path_name',
    (
        ('flows', 'does_not_exist', 'sentencizer.env'),
        ('flows', 'with-envs.yml', 'does_not_exist.env'),
        ('flows', '', 'does_not_even_exist.env'),
        ('flows', '', ''),
        ('flows', '', 'with-envs.yml'),
    ),
    ids=[
        'non_existed_path',
        'non_existed_env_file_with_valid_path_case1',
        'non_existed_env_file_with_valid_path_case2',
        'env_file_being_dir',
        'env_file_with_wrong_extension',
    ],
)
def test_invalid_path(parent_dir, path_name, env_path_name):
    with pytest.raises(SystemExit):
        flow = CloudFlow(
            path=os.path.join(cur_dir, '..', 'integration', parent_dir, path_name),
            env_file=os.path.join(
                cur_dir, '..', 'integration', parent_dir, env_path_name
            ),
        )


def test_no_env():
    flow = CloudFlow(
        path=os.path.join(cur_dir, '..', 'integration', 'flows', 'with-envs.yml'),
    )
    assert flow.envs == {}
