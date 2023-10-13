import os

from jcloud.deployment import CloudDeployment
from jcloud.constants import Phase

from tests.utils import utils
from .. import DeploymentAlive

deployments_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'deployments'
)
deployment_file = 'base_deployment.yml'
protocol = 'grpc'
executor_name = 'executor'


def test_scale_deployment():
    with CloudDeployment(
        path=os.path.join(deployments_dir, deployment_file)
    ) as deployment:
        assert utils.eventually_reaches_phase(deployment, Phase.Serving)

        assert deployment.endpoints != {}
        assert executor_name in deployment.endpoints
        gateway = deployment.endpoints[executor_name]
        assert gateway.startswith(f'{protocol}s://')

        ltt = utils.get_last_transition_time(deployment, DeploymentAlive)
        assert ltt

        assert utils.eventually_serve_requests(gateway)

        # scale executor to 2 replicas
        deployment._loop.run_until_complete(deployment.scale(replicas=2))
        assert utils.eventually_reaches_phase(deployment, Phase.Serving)
        assert utils.eventually_condition_gets_updated(deployment, DeploymentAlive, ltt)

        assert deployment.endpoints != {}
        assert executor_name in deployment.endpoints
        gateway = deployment.endpoints[executor_name]
        assert gateway.startswith(f'{protocol}s://')

        assert utils.eventually_serve_requests(gateway)

        status = deployment._loop.run_until_complete(deployment.status)
        assert status['spec']['with']['replicas'] == 2
