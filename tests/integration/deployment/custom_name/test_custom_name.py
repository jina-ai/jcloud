import os

import pytest
from jina import Client, Document, DocumentArray

from jcloud.deployment import CloudDeployment

deployments_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'deployments'
)
protocol = 'http'
executor_name = 'executor'


def test_valid_custom_name():
    valid_deployment_file = 'valid-name-deployment.yml'
    valid_custom_name = 'fashion-data'

    with CloudDeployment(
        path=os.path.join(deployments_dir, valid_deployment_file)
    ) as deployment:
        assert valid_custom_name in deployment.deployment_id
        assert deployment.endpoints != {}
        assert executor_name in deployment.endpoints
        endpoint = deployment.endpoints[executor_name]
        assert endpoint.startswith(f'{protocol}s://')
        assert valid_custom_name in endpoint

        da = Client(host=endpoint).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50


def test_invalid_custom_name(capsys):
    invalid_deployment_file = 'invalid-name-deployment.yml'
    invalid_custom_name = 'abc_def#1/'

    with pytest.raises(SystemExit):
        with CloudDeployment(
            path=os.path.join(deployments_dir, invalid_deployment_file)
        ):
            pass

    captured = capsys.readouterr()
    assert f'invalid name {invalid_custom_name}' in captured.out
