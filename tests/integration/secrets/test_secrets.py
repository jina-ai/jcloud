import os
import asyncio

from jcloud.flow import CloudFlow
from jcloud.constants import Resources

flows_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'basic', 'flows'
)
flow_file = 'http-flow.yml'


def test_create_secret():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:

        secret_response = asyncio.run(
            flow.create_secret('mysecret', {'env1': {'test': 'value'}})
        )
        assert 'name' in secret_response

        secret = asyncio.run(flow.get_resource(Resources.Secret, 'mysecret'))

        assert secret['name'] == 'mysecret'
        assert secret['data'] == {'test': 'value'}

        asyncio.run(flow.update_secret('mysecret', {'key': 'test2'}))

        secret = asyncio.run(flow.get_resource(Resources.Secret, 'mysecret'))

        assert secret['name'] == 'mysecret'
        assert secret['data'] == {'key': 'test2'}

        asyncio.run(flow.delete_resource(Resources.Secret, 'mysecret'))

        assert f'{flow_file.split(".")[0]}-mysecret.yml' in os.listdir(flows_dir)
