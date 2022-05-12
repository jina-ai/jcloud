import os

import pytest
from jcloud.flow import CloudFlow

cur_dir = os.path.dirname(os.path.abspath(__file__))


async def func(*args, **kwargs):
    return 'b'


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='non-interactive login not supported via GH Actions',
)
@pytest.mark.asyncio
async def test_post_params_non_existing_file(monkeypatch):
    flow = CloudFlow(path='invalid.yml')
    monkeypatch.setattr(flow, '_zip_and_upload', func)
    with pytest.raises(SystemExit):
        await flow._get_post_params()


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='non-interactive login not supported via GH Actions',
)
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


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='non-interactive login not supported via GH Actions',
)
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


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='non-interactive login not supported via GH Actions',
)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'dirname',
    (
        'testproject_simple',
        'testproject_multi_executors',
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


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='non-interactive login not supported via GH Actions',
)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'dirname',
    (
        'testproject_simple',
        'testproject_multi_executors',
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


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='non-interactive login not supported via GH Actions',
)
def test_valid_env():
    flow = CloudFlow(
        path=os.path.join(cur_dir, '..', 'integration', 'flows', 'with-envs.yml'),
        env_file=os.path.join(cur_dir, '..', 'integration', 'flows', 'sentencizer.env'),
    )
    assert flow.envs == {'PUNCT_CHARS': '(!,)'}


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='non-interactive login not supported via GH Actions',
)
def test_invalid_env():
    flow = CloudFlow(
        path=os.path.join(cur_dir, '..', 'integration', 'flows', 'with-envs.yml'),
        env_file=os.path.join(cur_dir, '..', 'integration', 'flows', 'invalid.env'),
    )
    with pytest.raises(SystemExit):
        flow.envs


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ,
    reason='non-interactive login not supported via GH Actions',
)
def test_no_env():
    flow = CloudFlow(
        path=os.path.join(cur_dir, '..', 'integration', 'flows', 'with-envs.yml'),
    )
    assert flow.envs == {}
