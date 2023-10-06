import os

import pytest
from jina import Client, Document, DocumentArray

from jcloud.flow import CloudFlow

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
protocol = 'grpc'


def test_valid_custom_name():
    valid_flow_file = 'valid-name.yml'
    valid_custom_name = 'fashion-data'

    with CloudFlow(path=os.path.join(flows_dir, valid_flow_file)) as flow:
        assert valid_custom_name in flow.flow_id
        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        assert gateway.startswith(f'{protocol}s://')
        assert valid_custom_name in gateway

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50


def test_invalid_custom_name(capsys):
    invalid_flow_file = 'invalid-name.yml'
    invalid_custom_name = 'abc_def#1/'

    with pytest.raises(SystemExit):
        with CloudFlow(path=os.path.join(flows_dir, invalid_flow_file)):
            pass

    captured = capsys.readouterr()
    assert f'invalid name {invalid_custom_name}' in captured.out
