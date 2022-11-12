import os

import pytest
from jina import Client, Document, DocumentArray

from jcloud.flow import CloudFlow

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'envs-in-flow.yml'


def test_yaml_env_file():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:
        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']

        da = Client(host=gateway).post(
            on='/',
            inputs=DocumentArray(Document(text='hello! There? abc')),
        )
        assert da[0].chunks[0].text == 'hello!'
        assert da[0].chunks[1].text == 'There? abc'
