import os

from jcloud.flow import CloudFlow
from jina import Client, Document, DocumentArray

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'flows')


def test_yaml_env_file():
    with CloudFlow(
        path=os.path.join(flows_dir, 'with-envs.yml'),
        name=f'sentencizer-envvars',
        env_file=os.path.join(flows_dir, 'sentencizer.env'),
    ) as flow:
        da = Client(host=flow.gateway).post(
            on='/',
            inputs=DocumentArray(Document(text='hello! There? abc')),
        )
        assert da[0].chunks[0].text == 'hello!'
        assert da[0].chunks[1].text == 'There? abc'
