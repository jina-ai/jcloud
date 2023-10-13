import os

from jcloud.deployment import CloudDeployment
from jcloud.constants import Phase

from tests.utils import utils

deployments_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'deployments'
)
protocol = 'grpc'
executor_name = 'executor'


def test_custom_labels():
    labels_file = 'deployment-with-labels.yml'
    with CloudDeployment(path=os.path.join(deployments_dir, labels_file)) as deployment:
        assert utils.eventually_reaches_phase(deployment, Phase.Serving)

        assert deployment.endpoints != {}
        assert executor_name in deployment.endpoints
        endpoint = deployment.endpoints[executor_name]
        assert endpoint.startswith(f'{protocol}s://')

        assert utils.eventually_serve_requests(endpoint)

        # TODO: check that the labels are actually set by searching for them
