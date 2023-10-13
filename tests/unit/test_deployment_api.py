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
    get,
)


async def mock_aexit(*args, **kwargs):
    pass


async def mock_list(*args, **kwargs):
    return {
        'deployments': [
            {'id': 'firm-condor-77f454eac2'},
            {'id': 'workable-shrew-f1bdd8f74b'},
            {'id': 'somename-1234567890'},
        ]
    }


async def mock_terminate(*args, **kwargs):
    return 'deployment-id'


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


async def mock_delete_resource(*args, **kwargs):
    pass


async def mock_create(*args, **kwargs):
    pass


async def mock_display(*args, **kwargs):
    pass


@patch('jcloud.api.CloudDeployment')
def test_deployment_remove_single(mock_clouddeployment):
    args = Mock()
    args.jc_cli = 'deployment'
    args.phase = None
    args.deployments = ['single_deployment_id']

    m = Mock()
    m.__aexit__ = Mock(side_effect=mock_aexit)
    mock_clouddeployment.return_value = m

    remove(args)

    mock_clouddeployment.assert_called_with(deployment_id='single_deployment_id')
    assert mock_clouddeployment.return_value.__aexit__.called == 1


@patch('rich.prompt.Confirm.ask', return_value=True)
@patch('jcloud.api._terminate_deployment_simplified')
@patch('jcloud.api._list_by_phase')
def test_deployment_remove_by_phase(
    mock_list_by_phase, mock_terminate_deployment_simplified, mock_ask
):
    args = Mock()
    args.jc_cli = 'deployment'
    args.phase = 'Serving'
    args.deployments = ['deployment_1', 'workable-shrew-f1bdd8f74b']
    mock_list_by_phase.side_effect = mock_list
    mock_terminate_deployment_simplified.side_effect = mock_terminate

    remove(args)
    mock_terminate_deployment_simplified.assert_has_calls(
        [
            call('deployment_1', 'Serving'),
            call('workable-shrew-f1bdd8f74b', args.phase),
            call('firm-condor-77f454eac2', args.phase),
            call('somename-1234567890', args.phase),
        ],
        any_order=True,
    )


@patch('rich.prompt.Confirm.ask', return_value=True)
@patch('jcloud.api._terminate_deployment_simplified')
@patch('jcloud.api._list_by_phase')
def test_deployment_remove_selected_multi(
    mock_list_by_phase, mock_terminate_deployment_simplified, mock_ask
):
    args = Mock()
    args.jc_cli = 'deployment'
    args.phase = None
    args.deployments = ['deployment_1', 'deployment_2']
    mock_list_by_phase.side_effect = mock_list
    mock_terminate_deployment_simplified.side_effect = mock_terminate

    remove(args)
    mock_terminate_deployment_simplified.assert_has_calls(
        [call('deployment_1', args.phase), call('deployment_2', args.phase)]
    )


@patch('rich.prompt.Confirm.ask', return_value=True)
@patch('jcloud.api._terminate_deployment_simplified')
@patch('jcloud.api._list_by_phase')
def test_deployment_remove_all(
    mock_list_by_phase, mock_terminate_deployment_simplified, mock_ask
):
    args = Mock()
    args.jc_cli = 'deployment'
    args.phase = None
    args.deployments = ['all']
    mock_list_by_phase.side_effect = mock_list
    mock_terminate_deployment_simplified.side_effect = mock_terminate

    remove(args)

    mock_terminate_deployment_simplified.assert_has_calls(
        [
            call('firm-condor-77f454eac2', args.phase),
            call('workable-shrew-f1bdd8f74b', args.phase),
            call('somename-1234567890', args.phase),
        ]
    )


@patch.dict(os.environ, {'JCLOUD_NO_INTERACTIVE': "1"}, clear=True)
@patch('jcloud.api._terminate_deployment_simplified')
@patch('jcloud.api._list_by_phase')
def test_deployment_non_interative(
    mock_list_by_phase, mock_terminate_deployment_simplified
):
    args = Mock()
    args.jc_cli = 'deployment'
    args.phase = None
    args.deployments = ['all']
    mock_list_by_phase.side_effect = mock_list
    mock_terminate_deployment_simplified.side_effect = mock_terminate

    remove(args)
    mock_terminate_deployment_simplified.assert_has_calls(
        [
            call('firm-condor-77f454eac2', args.phase),
            call('workable-shrew-f1bdd8f74b', args.phase),
            call('somename-1234567890', args.phase),
        ]
    )


@patch('jcloud.api.CloudDeployment')
def test_update(mock_clouddeployment):
    args = Mock()
    args.jc_cli = 'deployment'
    args.deployment = 'deployment'
    args.path = '/path/to/the/deployment'

    m = Mock()
    m.update = Mock(side_effect=mock_update)
    mock_clouddeployment.return_value = m

    update(args)

    mock_clouddeployment.assert_called_with(
        deployment_id='deployment', path='/path/to/the/deployment'
    )
    assert mock_clouddeployment.return_value.update.called == 1


@patch('jcloud.api.CloudDeployment')
def test_restart(mock_clouddeployment):
    args = Mock()
    args.jc_cli = 'deployment'
    args.deployment = 'deployment'

    m = Mock()
    m.restart = Mock(side_effect=mock_restart)
    mock_clouddeployment.return_value = m

    restart(args)

    mock_clouddeployment.assert_called_with(deployment_id='deployment')
    assert mock_clouddeployment.return_value.restart.called == 1


@patch('jcloud.api.CloudDeployment')
def test_pause(mock_clouddeployment):
    args = Mock()
    args.jc_cli = 'deployment'
    args.deployment = 'deployment'

    m = Mock()
    m.pause = Mock(side_effect=mock_pause)
    mock_clouddeployment.return_value = m

    pause(args)

    mock_clouddeployment.assert_called_with(deployment_id='deployment')
    assert mock_clouddeployment.return_value.pause.called == 1


@patch('jcloud.api.CloudDeployment')
def test_resume(mock_clouddeployment):
    args = Mock()
    args.jc_cli = 'deployment'
    args.deployment = 'deployment'

    m = Mock()
    m.resume = Mock(side_effect=mock_resume)
    mock_clouddeployment.return_value = m

    resume(args)

    mock_clouddeployment.assert_called_with(deployment_id='deployment')
    assert mock_clouddeployment.return_value.resume.called == 1


@patch('jcloud.api.CloudDeployment')
def test_scale(mock_clouddeployment):
    args = Mock()
    args.jc_cli = 'deployment'
    args.deployment = 'deployment'
    args.replicas = 2

    m = Mock()
    m.scale = Mock(side_effect=mock_scale)
    mock_clouddeployment.return_value = m

    scale(args)

    mock_clouddeployment.assert_called_with(deployment_id='deployment')
    mock_clouddeployment.return_value.scale.assert_called_once_with(replicas=2)


@patch('jcloud.api.CloudDeployment')
def test_recreate(mock_clouddeployment):
    args = Mock()
    args.jc_cli = 'deployment'
    args.deployment = 'deployment'

    m = Mock()
    m.recreate = Mock(side_effect=mock_recreate)
    mock_clouddeployment.return_value = m

    recreate(args)

    mock_clouddeployment.assert_called_with(deployment_id='deployment')
    assert mock_clouddeployment.return_value.recreate.called == 1


@patch('jcloud.api.CloudDeployment')
def test_deployment_logs(mock_clouddeployment):
    args = Mock()
    args.jc_cli = 'deployment'
    args.deployment = 'deployment'
    args.gateway = True

    m = Mock()
    m.logs = Mock(side_effect=mock_logs)
    mock_clouddeployment.return_value = m

    logs(args)

    mock_clouddeployment.assert_called_with(deployment_id='deployment')
    mock_clouddeployment.return_value.logs.assert_called_once()  # assert_has_calls([call()])
