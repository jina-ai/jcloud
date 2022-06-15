import os
import pytest

from unittest.mock import Mock, patch, call

from jcloud.api import remove, _get_status_table


async def mock_aexit(*args, **kwargs):
    pass


async def mock_list(*args, **kwargs):
    return [{'id': 'jflow-flow1'}, {'id': 'jflow-flow2'}, {'id': 'jflow-flow3'}]


async def mock_terminate(*args, **kwargs):
    return 'flow-id'


@patch('jcloud.api.CloudFlow')
def test_remove_single(mock_cloudflow):
    args = Mock()
    args.flows = ['single_flow_id']

    m = Mock()
    m.__aexit__ = Mock(side_effect=mock_aexit)
    mock_cloudflow.return_value = m

    remove(args)

    mock_cloudflow.assert_called_with(flow_id='single_flow_id')
    assert mock_cloudflow.return_value.__aexit__.called == 1


@patch('rich.prompt.Confirm.ask', return_value=True)
@patch('jcloud.api._terminate_flow_simplified')
@patch('jcloud.api._list_by_status')
def test_remove_selected_multi(
        mock_list_by_status, mock_terminate_flow_simplified, mock_ask
):
    args = Mock()
    args.flows = ['flow_1', 'flow_2']
    mock_list_by_status.side_effect = mock_list
    mock_terminate_flow_simplified.side_effect = mock_terminate

    remove(args)
    mock_terminate_flow_simplified.assert_has_calls([call('flow_1'), call('flow_2')])


@patch('rich.prompt.Confirm.ask', return_value=True)
@patch('jcloud.api._terminate_flow_simplified')
@patch('jcloud.api._list_by_status')
def test_remove_all(mock_list_by_status, mock_terminate_flow_simplified, mock_ask):
    args = Mock()
    args.flows = ['all']
    mock_list_by_status.side_effect = mock_list
    mock_terminate_flow_simplified.side_effect = mock_terminate

    remove(args)

    mock_terminate_flow_simplified.assert_has_calls(
        [call('flow1'), call('flow2'), call('flow3')]
    )


@patch.dict(os.environ, {'JCLOUD_NO_INTERACTIVE': "1"}, clear=True)
@patch('jcloud.api._terminate_flow_simplified')
@patch('jcloud.api._list_by_status')
def test_non_interative(mock_list_by_status, mock_terminate_flow_simplified):
    args = Mock()
    args.flows = ['all']
    mock_list_by_status.side_effect = mock_list
    mock_terminate_flow_simplified.side_effect = mock_terminate

    remove(args)
    mock_terminate_flow_simplified.assert_has_calls(
        [call('flow1'), call('flow2'), call('flow3')]
    )


@pytest.mark.parametrize('result', [
    [{
        'id': 'jflow-d8938ca2f3',
        'ctime': '2022-06-14T23:54:42.243000+00:00',
        'status': 'ALIVE',
        'gateway': 'https://nan-wang-docarray-d8938ca2f3.wolf.jina.ai',
        'endpoints': {
            'gateway': 'https://nan-wang-docarray-d8938ca2f3.wolf.jina.ai'
        }
    }, ], [{
        'id': 'jflow-4ee8e43ec7',
        'ctime': '2022-06-14T18:26:39.818000+00:00',
        'status': 'ALIVE',
        'gateway': None,
        'endpoints': {
            'questionfilterer': 'grpcs://questionfilterer-3h-4ee8e43ec7.wolf.jina.ai',
            'logger': 'grpcs://logger-pn-4ee8e43ec7.wolf.jina.ai'}
    }, ]])
def test__get_status_table(result):
    try:
        _get_status_table(result)
    except Exception:
        assert False, 'failed to create status table'
