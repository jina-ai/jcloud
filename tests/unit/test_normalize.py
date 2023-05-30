import os
import jina
import pytest

from unittest.mock import patch
from jcloud.normalize import *


@pytest.fixture
def cur_dir():
    return Path(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def workspace(cur_dir):
    return cur_dir / 'flows'


@pytest.fixture
def mixed_flow_path(workspace):
    return workspace / 'mixed_flow'


flow_data_params = ('normalized_flows', 'local_flow')


def test_failed_flow(cur_dir, workspace):
    flow_path = workspace / 'failed_flows' / 'failed_flow.yml'

    with pytest.raises(ValueError):
        load_flow_data(flow_path)

    with pytest.raises(FileNotFoundError):
        load_flow_data(cur_dir / 'failed_flow.yml')


def test_create_manifest():
    executor = ExecutorData(name='test', src_dir='/path/to/folder', tag='last')
    project_id = 'normalized_flow_test'
    generate_manifest(executor, project_id)


def test_get_hubble_url_with_executor_name():
    executor = ExecutorData(name='test', src_dir='/path/to/folder', tag='last')

    assert (
        get_hubble_uses(executor) == f'jinahub+docker://{executor.name}/{executor.tag}'
    )


def test_get_hubble_url_with_executor_id():
    executor = ExecutorData(id='1y0jd3ac', src_dir='/path/to/folder', tag='last')

    assert get_hubble_uses(executor) == f'jinahub+docker://{executor.id}/{executor.tag}'


@pytest.fixture(name='flow_data', params=flow_data_params)
def flow_data(request, workspace):
    flow_path = workspace / request.param / 'flow.yml'
    flow_data = load_flow_data(flow_path)
    assert flow_data['jtype'] == 'Flow'
    assert len(flow_data['executors']) == 2
    return flow_data, request.param


@pytest.fixture()
def executors(flow_data, workspace):
    result = inspect_executors(flow_data[0], workspace=workspace / flow_data[1])
    assert len(result) == 2
    if flow_data[1] == flow_data_params[0]:
        assert result[0].name == 'Executor1'
        assert result[0].hubble_url == 'jinahub+docker://Executor1'
        assert result[1].name == 'Executor2'
        assert result[1].hubble_url == 'jinahub+docker://Executor2'
    else:
        assert result[0].name == 'executor1-MyExecutor'
        assert result[0].src_dir == workspace / flow_data[1] / 'executor1'
        assert result[1].name == 'executor2-MyExecutor'
        assert result[1].src_dir == workspace / flow_data[1] / 'executor2'
    return result


def test_normalize_flow(flow_data, executors):
    flow = update_flow_data(flow_data[0], executors)

    if flow_data[1] == flow_data_params[0]:
        assert flow['executors'][0]['uses'] == 'jinahub+docker://Executor1'
        assert flow['executors'][1]['uses'] == 'jinahub+docker://Executor2'
    else:
        assert flow['executors'][0]['uses'] == 'jinahub+docker://executor1-MyExecutor'
        assert flow['executors'][1]['uses'] == 'jinahub+docker://executor2-MyExecutor'


@pytest.mark.parametrize('filename', ('flow1.yml', 'flow2.yml'))
def test_inspect_executors_without_uses(filename, cur_dir):
    flow_dir = os.path.join(cur_dir, 'flows')
    flow_dict = load_flow_data(Path(os.path.join(flow_dir, filename)))
    executors = inspect_executors(
        flow_dict=flow_dict, workspace=flow_dir, tag='abc', secret='abc'
    )
    assert executors[0].hubble_url == 'jinahub+docker://Sentencizer'
    assert executors[1].hubble_url == f'jinaai/jina:{jina.__version__}-py38-standard'
    assert executors[2].hubble_url == f'jinaai/jina:{jina.__version__}-py38-standard'


@pytest.mark.parametrize('filename', ('flow-with-labels.yml',))
def test_flow_labels_are_stringified(filename, cur_dir):
    flow_dir = os.path.join(cur_dir, 'flows')
    flow_dict = load_flow_data(Path(os.path.join(flow_dir, filename)))

    for _, label_value in flow_dict['jcloud']['labels'].items():
        assert isinstance(label_value, str)

    for _, label_value in flow_dict['executors'][0]['jcloud']['labels'].items():
        assert isinstance(label_value, str)


def test_mixed_update_flow_data(mixed_flow_path):
    flow_data = load_flow_data(mixed_flow_path / 'flow.yml')
    executors = inspect_executors(flow_data, mixed_flow_path, '', '')
    executors[0].id = '14mqmnk1'
    flow_data = update_flow_data(flow_data, executors)
    assert flow_data['executors'][0]['uses'] == f'jinahub+docker://{executors[0].id}'
    assert flow_data['executors'][1]['uses'] == 'jinahub+docker://Sentencizer'


@patch('jcloud.normalize.push_executors_to_hubble')
def test_flow_normalize_with_output_path(
    push_to_hubble_mock, mixed_flow_path, tmp_path
):
    for output_path in [None, tmp_path, tmp_path / 'hello.yml']:
        fn = flow_normalize(mixed_flow_path / 'flow.yml', output_path=output_path)
        assert os.path.isfile(fn)
        if output_path is not None and output_path.suffix == '.yml':
            assert os.path.isfile(output_path)
