import os
import shutil
import subprocess

from jcloud.flow import CloudFlow
from jina import Client, DocumentArray

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_jina_new():
    subprocess.run(["jina", "new", os.path.join(cur_dir, "hello-world")])

    assert os.path.exists(os.path.join(cur_dir, "hello-world"))
    assert os.path.isdir(os.path.join(cur_dir, "hello-world"))

    with CloudFlow(
        path=os.path.join(cur_dir, "hello-world"), name="hello-world"
    ) as flow:
        da = Client(host=flow.gateway).post(on="/", inputs=DocumentArray.empty(2))
        assert da.texts == ["hello, world!", "goodbye, world!"]

    shutil.rmtree(os.path.join(cur_dir, "hello-world"))

    assert not os.path.exists(os.path.join(cur_dir, "hello-world"))
