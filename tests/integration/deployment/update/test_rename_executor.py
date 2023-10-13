import os

from jcloud.deployment import CloudDeployment

from jcloud.helper import get_dict_list_key_path
from jcloud.constants import Phase

from tests.utils import utils
from .. import DeploymentAlive

deployments_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'deployments'
)
deployment_file = 'base_deployment.yml'
rename_executor_deployment_file = 'rename_executor.yml'
protocol = 'grpc'
executor_name = 'executor'


def test_rename_executor():
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

        deployment.path = os.path.join(deployments_dir, rename_executor_deployment_file)
        deployment._loop.run_until_complete(deployment.update())
        assert utils.eventually_reaches_phase(deployment, Phase.Serving)
        assert utils.eventually_condition_gets_updated(deployment, DeploymentAlive, ltt)

        new_name = 'newsentencizer'
        assert deployment.endpoints != {}
        assert new_name in deployment.endpoints
        endpoint = deployment.endpoints[new_name]
        assert endpoint.startswith(f'{protocol}s://')

        status = deployment._loop.run_until_complete(deployment.status)

        assert get_dict_list_key_path(status, ['spec', 'with', 'name']) == new_name

        assert utils.eventually_serve_requests(endpoint)
