import os

import pytest

from jcloud.flow import CloudFlow

cur_dir = os.path.dirname(os.path.abspath(__file__))


async def func(*args, **kwargs):
    return 'b'


@pytest.mark.asyncio
@pytest.mark.parametrize('filename', ('grpc-flow.yml', 'http-flow.yml'))
async def test_post_params_normalized_flow(monkeypatch, filename):
    flow = CloudFlow(
        path=os.path.join(cur_dir, '..', 'integration', 'basic', 'flows', filename)
    )
    monkeypatch.setattr(flow, '_zip_and_upload', func)
    _post_params = await flow._get_post_params()
    assert 'data' in _post_params
    assert len(_post_params['data']._fields) == 1
    assert _post_params['data']._fields[0][0]['name'] == 'spec'
    assert 'params' in _post_params
    assert _post_params['params'] == {}


@pytest.mark.asyncio
async def test_post_params_normalized_flow_with_env(monkeypatch):
    flow = CloudFlow(
        path=os.path.join(
            cur_dir, '..', 'integration', 'basic', 'flows', 'http-flow.yml'
        )
    )
    monkeypatch.setattr(flow, '_zip_and_upload', func)
    _post_params = await flow._get_post_params()
    assert 'data' in _post_params
    assert len(_post_params['data']._fields) == 1
    assert _post_params['data']._fields[0][0]['name'] == 'spec'
    assert 'params' in _post_params
    assert _post_params['params'] == {}


@pytest.mark.skip('unskip when normalized flow is implemented')
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


@pytest.mark.skip('unskip when normalized flow is implemented')
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
