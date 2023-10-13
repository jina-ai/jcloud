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
add_env_deployment_file = 'add_env.yml'
modify_env_deployment_file = 'modify_env.yml'
protocol = 'grpc'
executor_name = 'executor'


def test_update_executor_env():
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

        deployment.path = os.path.join(deployments_dir, add_env_deployment_file)
        deployment._loop.run_until_complete(deployment.update())
        assert utils.eventually_reaches_phase(deployment, Phase.Serving)
        assert utils.eventually_condition_gets_updated(deployment, DeploymentAlive, ltt)

        assert deployment.endpoints != {}
        assert executor_name in deployment.endpoints
        endpoint = deployment.endpoints[executor_name]
        assert endpoint.startswith(f'{protocol}s://')

        status = deployment._loop.run_until_complete(deployment.status)

        env = get_dict_list_key_path(status, ['spec', 'with', 'env'])

        assert 'JINA_LOG_LEVEL' in env and env['JINA_LOG_LEVEL'] == 'DEBUG'
        assert 'PUNCT_CHARS' in env and env['PUNCT_CHARS'] == '(!,)'

        assert utils.eventually_serve_requests(endpoint)

        ltt = utils.get_last_transition_time(deployment, DeploymentAlive)
        assert ltt
        deployment.path = os.path.join(deployments_dir, modify_env_deployment_file)
        deployment._loop.run_until_complete(deployment.update())
        assert utils.eventually_reaches_phase(deployment, Phase.Serving)
        assert utils.eventually_condition_gets_updated(deployment, DeploymentAlive, ltt)

        assert deployment.endpoints != {}
        assert executor_name in deployment.endpoints
        endpoint = deployment.endpoints[executor_name]
        assert endpoint.startswith(f'{protocol}s://')

        status = deployment._loop.run_until_complete(deployment.status)

        env = get_dict_list_key_path(status, ['spec', 'with', 'env'])

        assert 'JINA_LOG_LEVEL' in env and env['JINA_LOG_LEVEL'] == 'INFO'
        assert 'PUNCT_CHARS' not in env

        assert utils.eventually_serve_requests(endpoint)
