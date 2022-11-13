import os

import pytest
from jina import Client, Document

from jcloud.flow import CloudFlow

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.skip('unskip once autoscaling is implemented')
def test_customized_resources():
    FLOW_FILE_PATH = os.path.join(cur_dir, "flows", "executors-autoscaled.yml")
    with CloudFlow(path=FLOW_FILE_PATH, name="executors-autoscaled") as flow:
        da = Client(host=flow.gateway).post(
            on="/", inputs=Document(text="Hello. World.")
        )
        assert da[0].chunks[0].text == "Hello." and da[0].chunks[1].text == "World."
