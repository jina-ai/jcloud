import os
from unittest.mock import Mock, call, patch

from jcloud.api import (
    remove,
    update,
    restart,
    pause,
    resume,
    scale,
    recreate,
    logs,
    list,
    create,
    get,
)


async def mock_aexit(*args, **kwargs):
    pass


async def mock_list(*args, **kwargs):
    return {
        'flows': [
            {'id': 'firm-condor-77f454eac2'},
            {'id': 'workable-shrew-f1bdd8f74b'},
            {'id': 'somename-1234567890'},
        ]
    }


async def mock_terminate(*args, **kwargs):
    return 'flow-id'


async def mock_update(*args, **kwargs):
    pass


async def mock_restart(*args, **kwargs):
    pass


async def mock_pause(*args, **kwargs):
    pass


async def mock_resume(*args, **kwargs):
    pass


async def mock_scale(*args, **kwargs):
    pass


async def mock_recreate(*args, **kwargs):
    pass


async def mock_logs(*args, **kwargs):
    return {"pod_1": "logs\nlogs"}


async def mock_job_logs(*args, **kwargs):
    return 'test-job logs'


async def mock_list_jobs(*args, **kwargs):
    return [
        {'name': 'job-one', 'status': {'startTime': ''}},
        {'name': 'job-two', 'status': {'startTime': ''}},
        {'name': 'job-three', 'status': {'startTime': ''}},
    ]


async def mock_list_secrets(*args, **kwargs):
    return [
        {'name': 'secret-one', 'data': {'key': 'test'}},
        {'name': 'secret-two', 'data': {'key': 'test'}},
        {'name': 'secret-three', 'data': {'key': 'test'}},
    ]


async def mock_delete_resource(*args, **kwargs):
    pass


async def mock_create(*args, **kwargs):
    pass


async def mock_get_resource(*args, **kwargs):
    return {'name': 'test-secret', 'data': {'key': 'test'}}


def mock_display(*args, **kwargs):
    pass


@patch('jcloud.api.CloudFlow')
def test_flow_remove_single(mock_cloudflow):
    args = Mock()
    args.jc_cli = 'flow'
    args.phase = None
    args.flows = ['single_flow_id']

    m = Mock()
    m.__aexit__ = Mock(side_effect=mock_aexit)
    mock_cloudflow.return_value = m

    remove(args)

    mock_cloudflow.assert_called_with(flow_id='single_flow_id')
    assert mock_cloudflow.return_value.__aexit__.called == 1


@patch('rich.prompt.Confirm.ask', return_value=True)
@patch('jcloud.api._terminate_flow_simplified')
@patch('jcloud.api._list_by_phase')
def test_flow_remove_by_phase(
    mock_list_by_phase, mock_terminate_flow_simplified, mock_ask
):
    args = Mock()
    args.jc_cli = 'flow'
    args.phase = 'Serving'
    args.flows = ['flow_1', 'workable-shrew-f1bdd8f74b']
    mock_list_by_phase.side_effect = mock_list
    mock_terminate_flow_simplified.side_effect = mock_terminate

    remove(args)
    mock_terminate_flow_simplified.assert_has_calls(
        [
            call('flow_1', 'Serving'),
            call('workable-shrew-f1bdd8f74b', args.phase),
            call('firm-condor-77f454eac2', args.phase),
            call('somename-1234567890', args.phase),
        ],
        any_order=True,
    )


@patch('rich.prompt.Confirm.ask', return_value=True)
@patch('jcloud.api._terminate_flow_simplified')
@patch('jcloud.api._list_by_phase')
def test_flow_remove_selected_multi(
    mock_list_by_phase, mock_terminate_flow_simplified, mock_ask
):
    args = Mock()
    args.jc_cli = 'flow'
    args.phase = None
    args.flows = ['flow_1', 'flow_2']
    mock_list_by_phase.side_effect = mock_list
    mock_terminate_flow_simplified.side_effect = mock_terminate

    remove(args)
    mock_terminate_flow_simplified.assert_has_calls(
        [call('flow_1', args.phase), call('flow_2', args.phase)]
    )


@patch('rich.prompt.Confirm.ask', return_value=True)
@patch('jcloud.api._terminate_flow_simplified')
@patch('jcloud.api._list_by_phase')
def test_flow_remove_all(mock_list_by_phase, mock_terminate_flow_simplified, mock_ask):
    args = Mock()
    args.jc_cli = 'flow'
    args.phase = None
    args.flows = ['all']
    mock_list_by_phase.side_effect = mock_list
    mock_terminate_flow_simplified.side_effect = mock_terminate

    remove(args)

    mock_terminate_flow_simplified.assert_has_calls(
        [
            call('firm-condor-77f454eac2', args.phase),
            call('workable-shrew-f1bdd8f74b', args.phase),
            call('somename-1234567890', args.phase),
        ]
    )


@patch.dict(os.environ, {'JCLOUD_NO_INTERACTIVE': "1"}, clear=True)
@patch('jcloud.api._terminate_flow_simplified')
@patch('jcloud.api._list_by_phase')
def test_flow_non_interative(mock_list_by_phase, mock_terminate_flow_simplified):
    args = Mock()
    args.jc_cli = 'flow'
    args.phase = None
    args.flows = ['all']
    mock_list_by_phase.side_effect = mock_list
    mock_terminate_flow_simplified.side_effect = mock_terminate

    remove(args)
    mock_terminate_flow_simplified.assert_has_calls(
        [
            call('firm-condor-77f454eac2', args.phase),
            call('workable-shrew-f1bdd8f74b', args.phase),
            call('somename-1234567890', args.phase),
        ]
    )


@patch('jcloud.api.CloudFlow')
def test_update(mock_cloudflow):
    args = Mock()
    args.jc_cli = 'flow'
    args.flow = 'flow'
    args.path = '/path/to/the/flow'

    m = Mock()
    m.update = Mock(side_effect=mock_update)
    mock_cloudflow.return_value = m

    update(args)

    mock_cloudflow.assert_called_with(flow_id='flow', path='/path/to/the/flow')
    assert mock_cloudflow.return_value.update.called == 1


@patch('jcloud.api.CloudFlow')
def test_restart(mock_cloudflow):
    args = Mock()
    args.flow = 'flow'

    m = Mock()
    m.restart = Mock(side_effect=mock_restart)
    mock_cloudflow.return_value = m

    restart(args)

    mock_cloudflow.assert_called_with(flow_id='flow')
    assert mock_cloudflow.return_value.restart.called == 1


@patch('jcloud.api.CloudFlow')
def test_pause(mock_cloudflow):
    args = Mock()
    args.flow = 'flow'

    m = Mock()
    m.pause = Mock(side_effect=mock_pause)
    mock_cloudflow.return_value = m

    pause(args)

    mock_cloudflow.assert_called_with(flow_id='flow')
    assert mock_cloudflow.return_value.pause.called == 1


@patch('jcloud.api.CloudFlow')
def test_resume(mock_cloudflow):
    args = Mock()
    args.flow = 'flow'

    m = Mock()
    m.resume = Mock(side_effect=mock_resume)
    mock_cloudflow.return_value = m

    resume(args)

    mock_cloudflow.assert_called_with(flow_id='flow')
    assert mock_cloudflow.return_value.resume.called == 1


@patch('jcloud.api.CloudFlow')
def test_scale(mock_cloudflow):
    args = Mock()
    args.flow = 'flow'
    args.executor = 'ex'
    args.replicas = 2

    m = Mock()
    m.scale = Mock(side_effect=mock_scale)
    mock_cloudflow.return_value = m

    scale(args)

    mock_cloudflow.assert_called_with(flow_id='flow')
    mock_cloudflow.return_value.scale.assert_called_once_with(executor='ex', replicas=2)


@patch('jcloud.api.CloudFlow')
def test_recreate(mock_cloudflow):
    args = Mock()
    args.flow = 'flow'

    m = Mock()
    m.recreate = Mock(side_effect=mock_recreate)
    mock_cloudflow.return_value = m

    recreate(args)

    mock_cloudflow.assert_called_with(flow_id='flow')
    assert mock_cloudflow.return_value.recreate.called == 1


@patch('jcloud.api.CloudFlow')
def test_flow_logs(mock_cloudflow):
    args = Mock()
    args.jc_cli = 'flow'
    args.flow = 'flow'
    args.gateway = True

    m = Mock()
    m.logs = Mock(side_effect=mock_logs)
    mock_cloudflow.return_value = m

    logs(args)

    args.gateway = None
    args.executor = 'executor0'

    logs(args)

    mock_cloudflow.assert_called_with(flow_id='flow')
    mock_cloudflow.return_value.logs.assert_has_calls([call(), call('executor0')])


@patch('jcloud.api.CloudFlow')
def test_job_logs(mock_cloudflow):
    args = Mock()
    args.jc_cli = 'job'
    args.flow = 'flow'
    args.name = 'test-job'

    m = Mock()
    m.job_logs = Mock(side_effect=mock_job_logs)
    mock_cloudflow.return_value = m

    logs(args)

    mock_cloudflow.assert_called_with(flow_id='flow')
    mock_cloudflow.return_value.job_logs.assert_has_calls([call('test-job')])


@patch('jcloud.api.CloudFlow')
def test_job_secret_remove(mock_cloudflow):
    args = Mock()
    args.flow = 'flow'
    args.jc_cli = 'job'
    args.name = 'test-job'

    m = Mock()
    m.delete_resource = Mock(side_effect=mock_delete_resource)
    mock_cloudflow.return_value = m

    remove(args)

    args.jc_cli = 'secret'
    args.name = 'test-secret'

    remove(args)

    mock_cloudflow.assert_called_with(flow_id='flow')
    mock_cloudflow.return_value.delete_resource.assert_has_calls(
        [call('job', 'test-job'), call('secret', 'test-secret')]
    )
    assert mock_cloudflow.return_value.delete_resource.called == 1


@patch('jcloud.api.CloudFlow')
def test_job_secret_list(mock_cloudflow):
    args = Mock()
    args.jc_cli = 'secret'
    args.subcommand = 'list'
    args.flow = 'flow'

    m = Mock()
    m.list_resources = Mock(side_effect=mock_list_secrets)
    mock_cloudflow.return_value = m

    list(args)
    mock_cloudflow.assert_called_with(flow_id='flow')
    assert mock_cloudflow.return_value.list_resources.called == 1

    args.jc_cli = 'job'
    m.list_resources = Mock(side_effect=mock_list_jobs)
    mock_cloudflow.return_value = m
    list(args)

    mock_cloudflow.assert_called_with(flow_id='flow')
    assert mock_cloudflow.return_value.list_resources.called == 1


@patch('jcloud.api.CloudFlow')
def test_create_job(mock_cloudflow):
    args = Mock()
    args.flow = 'flow'
    args.jc_cli = 'job'
    args.name = 'test-job'
    args.image = 'image-name'
    args.timeout = 10
    args.backofflimit = 2
    args.entrypoint = 'ls'

    m = Mock()
    m.create_job = Mock(side_effect=mock_create)
    mock_cloudflow.return_value = m

    create(args)

    mock_cloudflow.assert_called_with(flow_id='flow')
    mock_cloudflow.return_value.create_job.assert_has_calls(
        [call('test-job', 'image-name', 10, 2, 'ls')]
    )


@patch('jcloud.api.CloudFlow')
def test_create_secret(mock_cloudflow):
    args = Mock()
    args.flow = 'flow'
    args.path = '/path/to/flow'
    args.jc_cli = 'secret'
    args.name = 'test-secret'
    args.from_literal = 'secret-value'
    args.update = True

    m = Mock()
    m.create_secret = Mock(side_effect=mock_create)
    mock_cloudflow.return_value = m

    create(args)

    mock_cloudflow.assert_called_with(flow_id='flow', path='/path/to/flow')
    mock_cloudflow.return_value.create_secret.assert_has_calls(
        [call('test-secret', 'secret-value', True)]
    )


@patch('jcloud.api._display_resources')
def test_get_resource_mock_display(mock_display_resources):
    args = Mock()
    args.flow = 'flow'
    args.jc_cli = 'secret'
    args.name = 'test-secret'

    mock_display_resources.side_effect = mock_display

    get(args)

    mock_display_resources.assert_has_calls([call(args)])


@patch('jcloud.api.CloudFlow')
def test_get_resource(mock_cloudflow):
    args = Mock()
    args.flow = 'flow'
    args.jc_cli = 'secret'
    args.name = 'test-secret'

    m = Mock()
    m.get_resource = Mock(side_effect=mock_get_resource)
    mock_cloudflow.return_value = m

    get(args)

    mock_cloudflow.assert_called_with(flow_id='flow')
    mock_cloudflow.return_value.get_resource.assert_has_calls(
        [call('secret', 'test-secret')]
    )


@patch('jcloud.api.CloudFlow')
def test_update_secret(mock_cloudflow):
    args = Mock()
    args.jc_cli = 'secret'
    args.flow = 'flow'
    args.name = 'test-secret'
    args.from_literal = 'secret-value'
    args.path = '/path/to/flow'
    args.update = True

    m = Mock()
    m.update_secret = Mock(side_effect=mock_update)
    mock_cloudflow.return_value = m

    update(args)

    mock_cloudflow.assert_called_with(flow_id='flow', path='/path/to/flow')
    mock_cloudflow.return_value.update_secret.assert_has_calls(
        [call('test-secret', 'secret-value', True)]
    )
