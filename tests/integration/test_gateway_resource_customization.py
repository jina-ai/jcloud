import os

from jcloud.flow import CloudFlow
from jina import Client, Document

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_customized_resources():
    FLOW_FILE_PATH = os.path.join(cur_dir, "flows", "resource-in-gateway.yml")
    with CloudFlow(path=FLOW_FILE_PATH, name="resource-in-gateway") as flow:
        da = Client(host=flow.gateway).post(
            on="/", inputs=Document(text="Hello. World.")
        )
        assert da[0].chunks[0].text == "Hello." and da[0].chunks[1].text == "World."
