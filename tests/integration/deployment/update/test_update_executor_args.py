import os

from jcloud.deployment import CloudDeployment
from jcloud.constants import Phase

from jcloud.helper import get_dict_list_key_path

from tests.utils import utils
from .. import DeploymentAlive

deployments_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'deployments'
)
deployment_file = 'base_deployment.yml'
new_exc_args_deployment_file = 'add_args.yml'
protocol = 'grpc'
executor_name = 'executor'


def test_update_executor_args():
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

        deployment.path = os.path.join(deployments_dir, new_exc_args_deployment_file)
        deployment._loop.run_until_complete(deployment.update())
        assert utils.eventually_reaches_phase(deployment, Phase.Serving)
        assert utils.eventually_condition_gets_updated(deployment, DeploymentAlive, ltt)

        assert deployment.endpoints != {}
        assert executor_name in deployment.endpoints
        endpoint = deployment.endpoints[executor_name]
        assert endpoint.startswith(f'{protocol}s://')

        status = deployment._loop.run_until_complete(deployment.status)
        assert (
            get_dict_list_key_path(status, ['spec', 'with', 'uses_with', 'punct_chars'])
            == '$PUNCT_CHARS'
        )

        assert utils.eventually_serve_requests(endpoint)
