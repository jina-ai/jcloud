import os

import pytest
from jina import Client, Document, DocumentArray

from jcloud.deployment import CloudDeployment

deployments_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'deployments'
)
protocol = 'grpc'
deployment_file = 'deployment-with-custom-resources.yml'
executor_name = 'c2instance'


def test_executor_resources():
    with CloudDeployment(
        path=os.path.join(deployments_dir, deployment_file)
    ) as deployment:
        assert deployment.endpoints != {}
        assert executor_name in deployment.endpoints
        endpoint = deployment.endpoints[executor_name]
        assert endpoint.startswith(f'{protocol}s://')

        da = Client(host=endpoint).post(
            on='/',
            inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
        )
        assert len(da.texts) == 50
