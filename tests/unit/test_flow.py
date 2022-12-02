import os
import tempfile

import pytest

import jcloud
from jcloud import flow  # import flow_normalize
from jcloud.flow import CloudFlow
from jcloud.normalize import flow_normalize

cur_dir = os.path.dirname(os.path.abspath(__file__))


def func(*args, **kwargs):
    return tempfile.mkstemp()[1]


@pytest.mark.asyncio
@pytest.mark.parametrize('filename', ('grpc-flow.yml', 'http-flow.yml'))
async def test_post_params_normalized_flow(monkeypatch, filename):
    flow = CloudFlow(
        path=os.path.join(cur_dir, '..', 'integration', 'basic', 'flows', filename)
    )
    monkeypatch.setattr('jcloud.normalize.flow_normalize', func)
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
    monkeypatch.setattr('jcloud.normalize.flow_normalize', func)
    _post_params = await flow._get_post_params()
    assert 'data' in _post_params
    assert len(_post_params['data']._fields) == 1
    assert _post_params['data']._fields[0][0]['name'] == 'spec'
    assert 'params' in _post_params
    assert _post_params['params'] == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'dirname',
    (
        'simple',
        # 'multi_executors',
        # 'envvars_default_file',
    ),
)
async def test_post_params_local_project_file(monkeypatch, dirname):
    flow = CloudFlow(
        path=os.path.join(cur_dir, '..', 'integration', 'projects', dirname, 'flow.yml')
    )
    monkeypatch.setattr('jcloud.normalize.flow_normalize', func)
    _post_params = await flow._get_post_params()
    assert 'data' in _post_params
    assert 'params' in _post_params


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'dirname',
    (
        'simple',
        'multi_executors',
        'envvars_default_file',
    ),
)
async def test_post_params_local_project_dir(monkeypatch, dirname):
    flow = CloudFlow(
        path=os.path.join(cur_dir, '..', 'integration', 'projects', dirname)
    )
    monkeypatch.setattr('jcloud.normalize.flow_normalize', func)
    _post_params = await flow._get_post_params()
    assert 'data' in _post_params
    assert 'params' in _post_params
