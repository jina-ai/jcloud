import os
import sys
import shutil
import subprocess
import tempfile

import pytest

from pathlib import Path
from venv import create
from jina import Client, DocumentArray
from jcloud.flow import CloudFlow

cur_dir = os.path.dirname(os.path.abspath(__file__))


def setup_venv():
    v_dir = Path(tempfile.mkdtemp())
    create(v_dir, with_pip=True)

    _pip_path = v_dir / 'bin' / 'pip'
    subprocess.run([_pip_path, 'install', '-U', 'pip', '-q'])
    subprocess.run([_pip_path, 'install', 'jina[standard]==3.18.0', '-q'])
    return v_dir


def test_jina_new_project():
    v_dir = setup_venv()
    subprocess.run(
        [v_dir / 'bin' / 'jina', 'new', os.path.join(cur_dir, 'hello-world')],
    )
    assert os.path.exists(os.path.join(cur_dir, 'hello-world'))
    assert os.path.isdir(os.path.join(cur_dir, 'hello-world'))

    with CloudFlow(path=os.path.join(cur_dir, 'hello-world')) as flow:
        assert flow.endpoints != {}
        assert 'gateway (grpc)' in flow.endpoints
        assert 'gateway (http)' in flow.endpoints
        assert 'gateway (websocket)' in flow.endpoints
        gateway = flow.endpoints['gateway (grpc)']

        da = Client(host=gateway).post(on='/', inputs=DocumentArray.empty(2))
        assert da.texts == ['hello, world!', 'goodbye, world!']

    shutil.rmtree(os.path.join(cur_dir, 'hello-world'))

    assert not os.path.exists(os.path.join(cur_dir, 'hello-world'))
