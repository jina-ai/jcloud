import os

import pytest
from jcloud.flow import CloudFlow
from jina import Client, Document

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.skip(
    reason="This test is currently not reliable due to https://github.com/jina-ai/jcloud/issues/45"
)
def test_executors_from_external_sources():
    FLOW_FILE_PATH = os.path.join(
        cur_dir, "flows", "executors-from-external-sources.yml"
    )
    with CloudFlow(path=FLOW_FILE_PATH, name="executors-from-external-sources") as flow:
        da = Client(host=flow.gateway).post(
            on="/", inputs=Document(text="Hello. World.")
        )
        assert da[0].chunks[0].text == "Hello." and da[0].chunks[1].text == "World."
