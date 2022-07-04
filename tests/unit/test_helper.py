import os

import pytest

from jcloud.helper import normalized, prepare_flow_model_for_render

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_invalid_file():
    with pytest.raises(FileNotFoundError):
        normalized(os.path.join(cur_dir, 'flows', 'normalized', 'nonexisting.yml'), {})


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
    assert normalized(os.path.join(cur_dir, 'flows', 'normalized', filename), envs)


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
    assert not normalized(os.path.join(cur_dir, 'flows', 'not', filename), envs)


@pytest.mark.parametrize(
    'response, expected',
    (
        (
            {
                'endpoints': 'something_can_be_ignored',
                'gateway': 'abc',
                'dashboards': None,
            },
            {'gateway': 'abc'},
        ),
        (
            {'endpoints': 'abc', 'gateway': None, 'dashboards': None},
            {'endpoints': 'abc'},
        ),
        (
            {
                'dashboards': {'monitoring': 'abc'},
                'gateway': 'abc',
                'endpoints': 'something_can_be_ignored',
            },
            {'dashboards': 'abc', 'gateway': 'abc'},
        ),
    ),
)
def test_prepare_flow_model_for_render(response, expected):
    prepare_flow_model_for_render(response)
    assert response == expected
