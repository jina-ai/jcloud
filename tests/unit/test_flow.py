import os

import pytest
from jcloud.flow import CloudFlow

cur_dir = os.path.dirname(os.path.abspath(__file__))


async def func(**kwargs):
    return 'b'


@pytest.mark.asyncio
async def test_post_params_non_existing_file(monkeypatch):
    flow = CloudFlow(path='invalid.yml')
    monkeypatch.setattr(flow, '_zip_and_upload', func)
    with pytest.raises(SystemExit):
        await flow._get_post_params()


@pytest.mark.asyncio
@pytest.mark.parametrize('filename', ('grpc-stateful.yml', 'http-stateful.yml'))
async def test_post_params_normalized_files(monkeypatch, filename):
    flow = CloudFlow(path=os.path.join(cur_dir, '..', 'integration', 'flows', filename))
    monkeypatch.setattr(flow, '_zip_and_upload', func)
    _post_params = await flow._get_post_params()
    assert 'data' in _post_params
    assert 'yaml' in _post_params['data']
    assert 'params' in _post_params
    assert _post_params['params'] == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'dirname',
    ('testproject1', 'testproject2', 'envvars_custom_file', 'envvars_default_file'),
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
    ('testproject1', 'testproject2', 'envvars_custom_file', 'envvars_default_file'),
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
