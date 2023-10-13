import os

from jcloud.deployment import CloudDeployment
from jcloud.constants import Phase

from tests.utils import utils

cur_dir = os.path.dirname(os.path.abspath(__file__))

protocol = 'http'
executor_name = 'executor'


# @pytest.mark.skip('unskip once autoscaling is implemented')
def test_autoscale_deployment():
    deployment_file_path = os.path.join(cur_dir, "deployments", "autoscale-http.yml")
    with CloudDeployment(path=deployment_file_path) as deployment:
        assert utils.eventually_reaches_phase(deployment, Phase.Serving)
        assert deployment.endpoints != {}
        assert executor_name in deployment.endpoints
        endpoint = deployment.endpoints[executor_name]
        assert endpoint.startswith(f'{protocol}s://')
        assert utils.eventually_serve_requests(endpoint)
