import os

import pytest
from jina import Client, Document, DocumentArray

from jcloud.deployment import CloudDeployment

deployments_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'deployments'
)
deployment_file = 'envvars.yml'
executor_name = 'executor'


def test_yaml_env_file():
    with CloudDeployment(
        path=os.path.join(deployments_dir, deployment_file)
    ) as deployment:
        assert deployment.endpoints != {}
        assert executor_name in deployment.endpoints
        endpoint = deployment.endpoints[executor_name]

        da = Client(host=endpoint).post(
            on='/',
            inputs=DocumentArray(Document(text='hello! There? abc')),
        )
        assert da[0].chunks[0].text == 'hello!'
        assert da[0].chunks[1].text == 'There? abc'
