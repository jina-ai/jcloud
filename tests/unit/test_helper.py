import os

import pytest
import tempfile
from jcloud.helper import normalized
from jcloud.env_helper import EnvironmentVariables
from jcloud.normalize import load_flow_data

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
