import os

import pytest
from jina import Client, Document

from jcloud.flow import CloudFlow

cur_dir = os.path.dirname(os.path.abspath(__file__))
flow_file = 'flow.yml'


def test_legacy_executor_syntax():
    with CloudFlow(path=os.path.join(cur_dir, flow_file)) as flow:
        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']

        da = Client(host=gateway).post(
            on='/',
            inputs=Document(text='Hello. World.'),
        )
        assert da[0].chunks[0].text == 'Hello.' and da[0].chunks[1].text == 'World.'
