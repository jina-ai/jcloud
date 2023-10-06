import os

from jina import Client, Document, DocumentArray

from jcloud.flow import CloudFlow

flows_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flows')
valid_flow_file = 'valid-flow.yml'
invalid_flow_file = 'invalid-flow.yml'


async def test_valid_flow():
    validate_response = await CloudFlow(
        path=os.path.join(flows_dir, valid_flow_file)
    ).validate()

    assert len(validate_response['errors']) == 0


async def test_invalid_flow():
    validate_response = await CloudFlow(
        path=os.path.join(flows_dir, invalid_flow_file)
    ).validate()
    assert len(validate_response['errors']) == 2
