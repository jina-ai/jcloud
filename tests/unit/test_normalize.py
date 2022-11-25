import os
import jina
import pytest

from jcloud.normalize import *

cur_dir = Path(os.path.dirname(os.path.abspath(__file__)))
workspace = cur_dir / 'flows'

project_id = 'normalized_flow_test'
flow_data_params = ('normalized_flows', 'local_flow')
mixed_flow_path = workspace / 'mixed_flow'


def test_failed_flow():
    flow_path = workspace / 'failed_flows' / 'failed_flow.yml'

    with pytest.raises(ValueError):
        load_flow_data(flow_path)

    with pytest.raises(FileNotFoundError):
        load_flow_data(cur_dir / 'failed_flow.yml')


def test_create_manifest():
    executor = ExecutorData(name='test', src_dir='/path/to/folder', tag='last')

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
def flow_data(request):
    flow_path = workspace / request.param / 'flow.yml'
    flow_data = load_flow_data(flow_path)
    assert flow_data['jtype'] == 'Flow'
    assert len(flow_data['executors']) == 2
    return flow_data, request.param


@pytest.fixture()
def executors(flow_data):
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


def test_flow_normalize(flow_data, executors):
    flow = normalize_flow(flow_data[0], executors)

    if flow_data[1] == flow_data_params[0]:
        assert flow['executors'][0]['uses'] == 'jinahub+docker://Executor1'
        assert flow['executors'][1]['uses'] == 'jinahub+docker://Executor2'
    else:
        assert flow['executors'][0]['uses'] == 'jinahub+docker://executor1-MyExecutor'
        assert flow['executors'][1]['uses'] == 'jinahub+docker://executor2-MyExecutor'


@pytest.mark.parametrize('filename', ('flow1.yml', 'flow2.yml'))
def test_inspect_executors_without_uses(filename):
    flow_dir = os.path.join(cur_dir, 'flows')
    flow_dict = load_flow_data(Path(os.path.join(flow_dir, filename)))
    executors = inspect_executors(
        flow_dict=flow_dict, workspace=flow_dir, tag='abc', secret='abc'
    )
    assert executors[0].hubble_url == 'jinahub+docker://Sentencizer'
    assert executors[1].hubble_url == f'jinaai/jina:{jina.__version__}-py38-standard'
    assert executors[2].hubble_url == f'jinaai/jina:{jina.__version__}-py38-standard'


def test_mixed_normalize_flow():
    flow_data = load_flow_data(mixed_flow_path / 'flow.yml')
    executors = inspect_executors(flow_data, mixed_flow_path, "", "")
    push_executors_to_hubble(executors)
    flow_data = normalize_flow(flow_data, executors)
    assert flow_data['executors'][0]['uses'] == f'jinahub+docker://{executors[0].id}'
    assert flow_data['executors'][1]['uses'] == 'jinahub+docker://Sentencizer'
