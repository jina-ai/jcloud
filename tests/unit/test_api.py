import os

from unittest.mock import Mock, patch, call

from jcloud.api import remove


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
