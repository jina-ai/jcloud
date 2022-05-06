import os

import pytest
from jcloud.helper import normalized

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_invalid_file():
    with pytest.raises(FileNotFoundError):
        normalized(os.path.join(cur_dir, 'flows', 'normalized', 'nonexisting.yml'))


@pytest.mark.parametrize(
    'filename',
    ('flow1.yml', 'flow2.yml', 'flow3.yml', 'flow4.yml', 'flow5.yml', 'flow6.yml'),
)
def test_normalized(filename):
    assert normalized(os.path.join(cur_dir, 'flows', 'normalized', filename))


@pytest.mark.parametrize(
    'filename',
    ('flow1.yml', 'flow2.yml', 'flow3.yml'),
)
def test_not_normalized(filename):
    assert not normalized(os.path.join(cur_dir, 'flows', 'not', filename))
