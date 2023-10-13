import os

import pytest

from jina import Client, Document, DocumentArray


from jcloud.constants import Phase
from jcloud.deployment import CloudDeployment

from tests.utils import utils
from .. import DeploymentAlive

deployments_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'deployments'
)
deployment_file = 'base_deployment.yml'
protocol = 'grpc'
executor_name = 'executor'


def test_pause_resume_deployment():
    with CloudDeployment(
        path=os.path.join(deployments_dir, deployment_file)
    ) as deployment:
        assert utils.eventually_reaches_phase(deployment, Phase.Serving)

        assert deployment.endpoints != {}
        assert executor_name in deployment.endpoints
        endpoint = deployment.endpoints[executor_name]
        assert endpoint.startswith(f'{protocol}s://')

        ltt = utils.get_last_transition_time(deployment, DeploymentAlive)
        assert ltt

        assert utils.eventually_serve_requests(endpoint)

        # pause the deployment
        deployment._loop.run_until_complete(deployment.pause())
        assert utils.eventually_reaches_phase(deployment, Phase.Paused)
        assert utils.eventually_condition_gets_updated(deployment, DeploymentAlive, ltt)

        assert deployment.endpoints != {}
        assert executor_name in deployment.endpoints
        endpoint = deployment.endpoints[executor_name]
        assert endpoint.startswith(f'{protocol}s://')

        with pytest.raises(ConnectionError):
            da = Client(host=endpoint).post(
                on='/',
                inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
            )

        # resume the deployment
        ltt = utils.get_last_transition_time(deployment, DeploymentAlive)
        assert ltt

        deployment._loop.run_until_complete(deployment.resume())
        assert utils.eventually_reaches_phase(deployment, Phase.Serving)
        assert utils.eventually_condition_gets_updated(deployment, DeploymentAlive, ltt)

        assert deployment.endpoints != {}
        assert executor_name in deployment.endpoints
        endpoint = deployment.endpoints[executor_name]
        assert endpoint.startswith(f'{protocol}s://')

        assert utils.eventually_serve_requests(endpoint)
