import os

from jina import Client, Document

from jcloud.deployment import CloudDeployment

deployments_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'deployments'
)
deployment_file = 'deployment-3.21.0.yml'
executor_name = 'executor'


def test_expose_version_arg():
    with CloudDeployment(
        path=os.path.join(deployments_dir, deployment_file)
    ) as deployment:
        assert deployment.endpoints != {}
        assert executor_name in deployment.endpoints
        endpoint = deployment.endpoints[executor_name]
        da = Client(host=endpoint).post(on="/", inputs=Document(text="Hello. World."))
        assert da[0].chunks[0].text == "Hello." and da[0].chunks[1].text == "World."
