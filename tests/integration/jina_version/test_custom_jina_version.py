import os

from jina import Client, Document

from jcloud.flow import CloudFlow

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
flow_file = 'custom-jina-version.yml'


def test_expose_version_arg():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:
        assert flow.endpoints != {}
        assert 'gateway' in flow.endpoints
        gateway = flow.endpoints['gateway']
        da = Client(host=gateway).post(on="/", inputs=Document(text="Hello. World."))
        assert da[0].chunks[0].text == "Hello." and da[0].chunks[1].text == "World."
