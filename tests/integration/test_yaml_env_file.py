import os

import pytest
from jcloud.flow import CloudFlow
from jina import Client, Document, DocumentArray

cur_dir = os.path.dirname(os.path.abspath(__file__))


# @pytest.mark.skip('non-interactive login not supported yet')
def test_yaml_env_file():
    with CloudFlow(
        path=os.path.join(cur_dir, 'flows', 'with-envs.yml'),
        name=f'sentencizer-envvars',
        env_file=os.path.join(cur_dir, 'flows', 'sentencizer.env'),
    ) as flow:
        da = Client(host=flow.gateway).post(
            on='/',
            inputs=DocumentArray(Document(text='hello! There? abc')),
        )
        assert da[0].chunks[0].text == 'hello!'
        assert da[0].chunks[1].text == 'There? abc'
