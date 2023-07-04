import os

import pytest
import tempfile

from pathlib import Path

from jcloud.helper import (
    normalized,
    load_flow_data,
    JCloudLabelsError,
    update_flow_yml_and_write_to_file,
)
from jcloud.env_helper import EnvironmentVariables

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_invalid_file():
    with pytest.raises(FileNotFoundError):
        normalized(os.path.join(cur_dir, 'flows', 'normalized', 'nonexisting.yml'))


@pytest.mark.parametrize(
    'filename, envs',
    (
        ('flow1.yml', {}),
        ('flow2.yml', {}),
        ('flow3.yml', {}),
        ('flow4.yml', {}),
        ('flow5.yml', {}),
        ('flow6.yml', {}),
        ('flow7.yml', {'E1_USES': 'jinahub+docker://E1'}),
        ('flow8.yml', {'E1_USES': 'jinahub+docker://E1'}),
        ('flow9.yml', {'E1_USES': 'jinahub+docker://E1'}),
    ),
)
def test_normalized(filename, envs):
    from jina.jaml import JAML

    if filename == 'flow7.yml':
        with EnvironmentVariables(envs) as _:
            flow_dict = load_flow_data(
                os.path.join(cur_dir, 'flows', 'normalized_flows', filename),
                envs,
            )
    else:
        flow_dict = load_flow_data(
            os.path.join(cur_dir, 'flows', 'normalized_flows', filename),
            envs,
        )
    with tempfile.NamedTemporaryFile('w') as f:
        JAML.dump(flow_dict, stream=f)
        assert normalized(f.name)


@pytest.mark.parametrize(
    'filename, envs',
    (
        ('flow1.yml', {}),
        ('flow2.yml', {}),
        ('flow3.yml', {}),
        ('flow4.yml', {'E1_USES': 'some invalid URL'}),
    ),
)
def test_not_normalized(filename, envs):
    from jina.jaml import JAML

    flow_dict = load_flow_data(
        os.path.join(cur_dir, 'flows', 'not', filename),
        envs,
    )

    with tempfile.NamedTemporaryFile('w') as f:
        JAML.dump(flow_dict, stream=f)
        assert not normalized(f.name)


def test_failed_flow():
    flow_path = Path(cur_dir) / 'flows' / 'failed_flows' / 'failed_flow.yml'

    with pytest.raises(ValueError):
        load_flow_data(flow_path)

    with pytest.raises(FileNotFoundError):
        load_flow_data(Path(cur_dir) / 'failed_flow.yml')


@pytest.mark.parametrize(
    'filename', ('flow-with-labels.yml', 'flow-with-obj-label.yml')
)
def test_flow_labels_are_stringified(filename):
    flow_dir = os.path.join(cur_dir, 'flows')
    if filename == 'flow-with-obj-label.yml':
        with pytest.raises(JCloudLabelsError) as exc_info:
            flow_dict = load_flow_data(Path(os.path.join(flow_dir, filename)))
            assert 'dict' in exc_info.value
    else:
        flow_dict = load_flow_data(Path(os.path.join(flow_dir, filename)))
        for _, label_value in flow_dict['jcloud']['labels'].items():
            assert isinstance(label_value, str)

        for _, label_value in flow_dict['executors'][0]['jcloud']['labels'].items():
            assert isinstance(label_value, str)


def test_update_flow_yml_and_write_to_file():
    flow_path = Path(os.path.join(cur_dir, 'flows', 'flow1.yml'))
    flow_path_with_secret = update_flow_yml_and_write_to_file(
        flow_path,
        'test',
        {'env1': 'secret-key', 'env2': 'secret-value'},
    )
    flow_data = load_flow_data(flow_path_with_secret)
    assert 'with' in flow_data
    assert 'env_from_secret' in flow_data['with']
    assert flow_data['with']['env_from_secret'] == {
        'env1': {'key': 'env1', 'name': 'test'},
        'env2': {'key': 'env2', 'name': 'test'},
    }
