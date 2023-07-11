import os
import pip
import shutil
import subprocess

import pytest

from jcloud.flow import CloudFlow
from jina import Client

cur_dir = os.path.dirname(os.path.abspath(__file__))


def test_jina_new():
    subprocess.run(['jina', 'new', os.path.join(cur_dir, 'hello-world')])
    import docarray

    print(docarray.__version__)
    subprocess.run(['pip', 'install', '-U', 'docarray', '-q'])
    docarray = __import__('docarray')

    print(docarray.__version__)
    from docarray import DocList
    from docarray.documents import TextDoc

    assert os.path.exists(os.path.join(cur_dir, 'hello-world'))
    assert os.path.isdir(os.path.join(cur_dir, 'hello-world'))

    with CloudFlow(path=os.path.join(cur_dir, "hello-world")) as flow:
        assert flow.endpoints != {}
        assert 'gateway (grpc)' in flow.endpoints
        assert 'gateway (http)' in flow.endpoints
        assert 'gateway (websocket)' in flow.endpoints
        gateway = flow.endpoints['gateway (grpc)']

        da = Client(host=gateway).post(
            on='/', inputs=DocList[TextDoc](TextDoc() for i in range(2))
        )
        assert da[0].text == ['hello, world!']
        assert da[1].text == ['goodbye, world!']

    shutil.rmtree(os.path.join(cur_dir, "hello-world"))

    assert not os.path.exists(os.path.join(cur_dir, "hello-world"))
