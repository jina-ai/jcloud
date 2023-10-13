import asyncio
import os

from functools import wraps
from typing import Dict
from argparse import Namespace

from .constants import (
    Phase,
    DASHBOARD_FLOW_URL_MARKDOWN,
    DASHBOARD_DEPLOYMENT_URL_MARKDOWN,
    Resources,
)
from .flow import CloudFlow, _terminate_flow_simplified
from .deployment import CloudDeployment, _terminate_deployment_simplified
from .helper import (
    cleanup_dt,
    get_cph_from_response,
    get_phase_from_response,
    get_str_endpoints_from_response,
    jsonify,
    yamlify,
    get_or_reuse_loop,
    exit_if_flow_defines_secret,
)
from .normalize import flow_normalize


def asyncify(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return get_or_reuse_loop().run_until_complete(f(*args, **kwargs))

    return wrapper


@asyncify
async def deploy(args):
    if Resources.Flow in args.jc_cli:
        exit_if_flow_defines_secret(args.path)
        return await CloudFlow(path=args.path).__aenter__()
    elif Resources.Deployment in args.jc_cli:
        # exit_if_deployment_defines_secret(args.path)
        return await CloudDeployment(path=args.path).__aenter__()


def normalize(args):
    flow_normalize(path=args.path, verbose=args.verbose, output_path=args.output)


@asyncify
async def status(args):
    from rich import box
    from rich.console import Console
    from rich.json import JSON
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.markdown import Markdown

    from .helper import CustomHighlighter, add_table_row_fn, center_align

    _t = Table(
        'Attribute',
        'Value',
        show_header=False,
        box=box.ROUNDED,
        highlight=True,
        show_lines=True,
    )

    console = Console(highlighter=CustomHighlighter())
    if args.jc_cli == Resources.Flow:
        res = args.flow
        dashboard = Markdown(
            DASHBOARD_FLOW_URL_MARKDOWN.format(flow_id=args.flow),
            justify='center',
        )
    elif args.jc_cli == Resources.Deployment:
        res = args.deployment
        dashboard = Markdown(
            DASHBOARD_DEPLOYMENT_URL_MARKDOWN.format(deployment_id=args.deployment),
            justify='center',
        )
    else:
        console.print(
            f'[red]Something went wrong while fetching the details ![/red]. Please retry after sometime.'
        )
        return

    with console.status(f'[bold]Fetching status of [green]{res}[/green] ...'):
        if args.jc_cli == Resources.Flow:
            _result = await CloudFlow(flow_id=res).status
        elif args.jc_cli == Resources.Deployment:
            _result = await CloudDeployment(deployment_id=res).status
        if not _result:
            console.print(
                f'[red]Something went wrong while fetching the details for {res} ![/red]. Please retry after sometime.'
            )
        else:
            _other_rows = []
            for k, v in _result.items():
                if k == 'id':
                    _id_row = add_table_row_fn(_t, 'ID', center_align(v))

                elif k == 'status':
                    for _k, _v in v.items():
                        if _k == 'phase':
                            # Show Phase
                            _phase_row = add_table_row_fn(_t, 'Phase', center_align(_v))

                        elif _k == 'endpoints' and _v:
                            # Show Endpoints and Dashboards
                            _other_rows.append(
                                add_table_row_fn(_t, 'Endpoint(s)', JSON(jsonify(_v)))
                            )

                        elif _k == 'dashboards' and _v:
                            # Show Dashboard
                            _other_rows.append(
                                add_table_row_fn(
                                    _t,
                                    'Dashboard',
                                    dashboard,
                                )
                            )

                        elif _k == 'conditions' and args.verbose:
                            # Show Conditions only if verbose
                            _other_rows.append(
                                add_table_row_fn(_t, 'Details', JSON(jsonify(_v)))
                            )

                        elif _k == 'version' and args.verbose:
                            # Show Jina version only if verbose
                            _other_rows.append(
                                add_table_row_fn(_t, 'Jina Version', center_align(_v))
                            )

                elif k == 'spec' and v is not None:
                    v = Syntax(
                        yamlify(v),
                        'yaml',
                        theme='monokai',
                        line_numbers=1,
                        code_width=60,
                    )
                    _other_rows.append(add_table_row_fn(_t, 'Spec', v))

                elif k == 'CPH' and v:
                    _other_rows.append(
                        add_table_row_fn(_t, 'Credits Per Hour', JSON(jsonify(v)))
                    )

                elif k == 'error' and v:
                    _other_rows.append(add_table_row_fn(_t, k, f'[red]{v}[red]'))

                elif k in ('ctime', 'utime'):
                    _other_rows.append(
                        add_table_row_fn(
                            _t,
                            'Created' if k == 'ctime' else 'Updated',
                            center_align(cleanup_dt(v)),
                        ),
                    )

            for fn in [_id_row, _phase_row, *_other_rows]:
                fn()
            console.print(_t)


async def _list_by_phase(
    phase: str, name: str, labels: Dict[str, str], jc_cli: Resources = Resources.Flow
):
    from rich import box
    from rich.console import Console
    from rich.table import Table

    from .helper import CustomHighlighter

    _t = Table(
        'ID',
        'Status',
        'Endpoint(s)',
        'Credits Per Hour',
        'Created',
        box=box.ROUNDED,
        highlight=True,
    )

    console = Console(highlighter=CustomHighlighter())

    # If no phase is passed, show all flows that are not in `Deleted` phase
    if phase is None:
        phase_to_str = lambda phase: str(phase.value)
        phase = ','.join(
            [
                phase_to_str(Phase.Starting),
                phase_to_str(Phase.Serving),
                phase_to_str(Phase.Failed),
                phase_to_str(Phase.Updating),
                phase_to_str(Phase.Paused),
            ]
        )
    if labels is not None:
        labels = labels.replace(',', '&')
    phases = phase.split(',')

    msg = f'[bold]Fetching [green]{phases[0] if len(phases) == 1 else ", ".join(phases)}[/green] {jc_cli}s'
    if name:
        msg += f' with name [green]{name}[/green]'
    msg += ' ...'
    with console.status(msg):
        _res = dict()
        if jc_cli == Resources.Flow:
            _result = await CloudFlow().list_all(phase=phase, name=name, labels=labels)
            if _result and 'flows' in _result:
                _res = _result['flows']
        elif jc_cli == Resources.Deployment:
            _result = await CloudDeployment().list_all(
                phase=phase, name=name, labels=labels
            )
            if _result and 'deployments' in _result:
                _res = _result['deployments']

        for resource in _res:
            _t.add_row(
                resource['id'],
                get_phase_from_response(resource),
                get_str_endpoints_from_response(resource),
                get_cph_from_response(resource),
                cleanup_dt(resource['ctime']),
            )
        console.print(_t)
    return _result


async def _display_resources(args: Namespace):
    from rich import box
    from rich.console import Console
    from rich.json import JSON
    from rich.table import Table

    if Resources.Job in args.jc_cli:
        _t = Table(
            f'{Resources.Job.title()} Name',
            'Status',
            'Start Time',
            'Completion Time',
            'Last Probe Time',
            box=box.ROUNDED,
            highlight=True,
        )
    else:
        _t = Table(
            f'{Resources.Secret.title()} Name',
            'Data',
            box=box.ROUNDED,
            highlight=True,
        )
    resource_type = Resources.Job if Resources.Job in args.jc_cli else Resources.Secret
    console = Console()
    if args.subcommand == 'list':
        msg = f'[bold]Listing {resource_type.title()}s for flow [green]{args.flow}[/green]'
    else:
        msg = f'[bold]Retrieving {resource_type.title()} [green]{args.name}[/green] for flow [green]{args.flow}[/green]'
    with console.status(msg):
        if args.subcommand == 'list':
            resources = await CloudFlow(flow_id=args.flow).list_resources(args.jc_cli)
        else:
            resource = await CloudFlow(flow_id=args.flow).get_resource(
                args.jc_cli, args.name
            )
            resources = [resource]
        for resource in resources:
            resource_name = resource['name']
            if Resources.Job in resource_type:
                _t.add_row(
                    resource_name,
                    resource['status']['conditions'][-1]['type']
                    if resource['status'].get('conditions')
                    else 'Pending',
                    cleanup_dt(resource['status']['startTime']),
                    cleanup_dt(resource['status'].get('completionTime', 'N/A')),
                    cleanup_dt(
                        resource['status']['conditions'][-1]['lastProbeTime']
                        if resource['status'].get('conditions')
                        else 'N/A'
                    ),
                )
            else:
                _t.add_row(
                    resource_name,
                    JSON(jsonify(resource['data'])),
                )
        console.print(_t)


@asyncify
async def list(args):
    if Resources.Flow in args.jc_cli or Resources.Deployment in args.jc_cli:
        await _list_by_phase(args.phase, args.name, args.labels, args.jc_cli)
    else:
        await _display_resources(args)


@asyncify
async def remove(args):
    from rich import print
    from rich.prompt import Confirm

    if Resources.Flow in args.jc_cli or Resources.Deployment in args.jc_cli:
        resources = set()
        res_key = ""
        if Resources.Flow in args.jc_cli:
            if not args.flows:
                print('[cyan]Please pass in flow(s) to remove. Exiting...[/cyan]')
                return
            resources = args.flows
            res_key = "flows"

        if Resources.Deployment in args.jc_cli:
            if not args.deployments:
                print('[cyan]Please pass in deployment(s) to remove. Exiting...[/cyan]')
                return
            resources = args.deployments
            res_key = "deployments"

        if args.phase is not None:
            _raw_list = await _list_by_phase(args.phase, '', None)
            res_id_list = [res['id'] for res in _raw_list[res_key]]
            res_set_diff = set(res_id_list).difference(resources)
            resources.extend(res_set_diff)

        # Case 1: remove single flow/deployment, using full progress bar.
        if len(resources) == 1 and resources != ['all']:
            if Resources.Flow in args.jc_cli:
                await CloudFlow(flow_id=resources[0]).__aexit__()
                print(f'Successfully removed Flow [green]{resources[0]}[/green].')
            elif Resources.Deployment in args.jc_cli:
                await CloudDeployment(deployment_id=resources[0]).__aexit__()
                print(f'Successfully removed Deployment [green]{resources[0]}[/green].')
            return

        # Case 2: remove a list of selected flows, using simplied progress bar.
        if len(resources) > 1:
            if 'JCLOUD_NO_INTERACTIVE' not in os.environ:
                confirmation_message_details = '\n'.join(resources)
                confirm_deleting_all = Confirm.ask(
                    f'Selected {res_key}: \n[red]{confirmation_message_details}\n\nAre you sure you want to delete above {res_key}? [/red]'
                )
                if not confirm_deleting_all:
                    print('[cyan]No worries. Exiting...[/cyan]')
                    return

        # Case 3: remove all SERVING and FAILED flows.
        else:
            if 'JCLOUD_NO_INTERACTIVE' not in os.environ:
                confirm_deleting_all = Confirm.ask(
                    f'[red]Are you sure you want to delete ALL the SERVING and FAILED {res_key} that belong to you?[/red]',
                    default=True,
                )
                if not confirm_deleting_all:
                    print('[cyan]No worries. Exiting...[/cyan]')
                    return

            if Resources.Deployment in args.jc_cli:
                _raw_list = await _list_by_phase(
                    phase=','.join([str(Phase.Serving.value), str(Phase.Failed.value)]),
                    name='',
                    labels=None,
                    jc_cli=Resources.Deployment,
                )
            else:
                _raw_list = await _list_by_phase(
                    phase=','.join([str(Phase.Serving.value), str(Phase.Failed.value)]),
                    name='',
                    labels=None,
                )
            print(f'Above are the {res_key} about to be deleted.\n')

            if 'JCLOUD_NO_INTERACTIVE' not in os.environ:
                confirm_deleting_again = Confirm.ask(
                    '[red]Are you sure you want to delete them?[/red]', default=True
                )
                if not confirm_deleting_again:
                    print('[cyan]No worries. Exiting...[/cyan]')
                    return

            resources = [res['id'] for res in _raw_list[res_key]]

        await _remove_multi(resources, args.phase, args.jc_cli)
    else:
        await CloudFlow(flow_id=args.flow).delete_resource(args.jc_cli, args.name)

        print(f'Successfully removed {args.jc_cli} with name {args.name}')


async def _remove_multi(res_id_list, phase, jc_cli: Resources = Resources.Flow):
    from rich import print

    from .helper import get_pbar

    num_res_to_remove = len(res_id_list)
    pbar, pb_task = get_pbar(
        '', total=num_res_to_remove, disable='JCLOUD_NO_PROGRESSBAR' in os.environ
    )

    with pbar:
        pbar.start_task(pb_task)
        pbar.update(
            pb_task,
            description='Starting',
            title=f'Removing {num_res_to_remove} flows...',
        )

        if Resources.Deployment in jc_cli:
            coros = [
                _terminate_deployment_simplified(deployment, phase)
                for deployment in res_id_list
            ]
            res_name = "deployment"
        else:
            coros = [_terminate_flow_simplified(flow, phase) for flow in res_id_list]
            res_name = "flow"
        counter = 0
        has_failure_task = False
        for coro in asyncio.as_completed(coros):
            try:
                res_id = await coro
                counter += 1
                print(f'[red]{res_id} removed![/red]')
                pbar.update(
                    pb_task,
                    advance=1,
                    description=f'Last {res_name} removed: [red]{res_id}[/red]. {num_res_to_remove - counter} {res_name}(s) to go',
                )
            except:
                has_failure_task = True
        if Resources.Deployment in jc_cli:
            await CloudDeployment._cancel_pending()
        else:
            await CloudFlow._cancel_pending()

    if has_failure_task:
        print(f'Some {res_name}s were not removed properly, please check!')
    else:
        print(f'Successfully removed {res_name}s listed above.')


def login(args):
    import hubble

    hubble.login(prompt='login')


def logout(args):
    import hubble

    hubble.logout()


def new(args):
    import os
    import shutil
    import sys

    rp = os.path.join(os.path.dirname(sys.modules['jcloud'].__file__), 'resources')

    shutil.copytree(os.path.join(rp, 'project-template'), os.path.abspath(args.path))

    from rich import print

    print(
        f'[green]New project created under {args.path}[/green]. Try [b]jc deploy {args.path}[/b].'
    )


@asyncify
async def update(args):
    from rich import print

    if Resources.Flow in args.jc_cli:
        print(f'Updating Flow: [green]{args.flow}[/green]')
        await CloudFlow(flow_id=args.flow, path=args.path).update()
    elif Resources.Deployment in args.jc_cli:
        print(f'Updating Deployment: [green]{args.deployment}[/green]')
        await CloudDeployment(deployment_id=args.deployment, path=args.path).update()
    else:
        await CloudFlow(flow_id=args.flow, path=args.path).update_secret(
            args.name, args.from_literal, args.update
        )
        print(
            f'Successfully updated Secret [green]{args.name}[/green]. Flow {args.flow} is restarting.'
        )


@asyncify
async def restart(args):
    from rich import print

    if Resources.Deployment in args.jc_cli:
        print(f'Restarting Deployment: [green]{args.deployment}[/green]')
        await CloudDeployment(deployment_id=args.deployment).restart()
        return

    if args.gateway:
        print(f'Restarting gateway of the Flow: [green]{args.flow}[/green]')
    elif args.executor:
        print(
            f'Restarting executor:[blue]{args.executor}[/blue] of the Flow: [green]{args.flow}[/green]'
        )
    else:
        print(f'Restarting Flow: [green]{args.flow}[/green]')
    await CloudFlow(flow_id=args.flow).restart(
        gateway=args.gateway, executor=args.executor
    )


@asyncify
async def pause(args):
    from rich import print

    if Resources.Deployment in args.jc_cli:
        print(f'Pausing Deployment: [green]{args.deployment}[/green]')
        await CloudDeployment(deployment_id=args.deployment).pause()
        return

    print(f'Pausing Flow: [orange3]{args.flow}[/orange3]')
    await CloudFlow(flow_id=args.flow).pause()


@asyncify
async def resume(args):
    from rich import print

    if Resources.Deployment in args.jc_cli:
        print(f'Resuming Deployment: [green]{args.deployment}[/green]')
        await CloudDeployment(deployment_id=args.deployment).resume()
        return

    print(f'Resuming Flow: [green]{args.flow}[/green]')
    await CloudFlow(flow_id=args.flow).resume()


@asyncify
async def scale(args):
    from rich import print

    if Resources.Deployment in args.jc_cli:
        print(
            f'Scaling Deployment: [green]{args.deployment}[/green] to {args.replicas} replicas'
        )
        await CloudDeployment(deployment_id=args.deployment).scale(
            replicas=args.replicas
        )
        return

    print(
        f'Scaling Executor: [red]{args.executor}[/red] of the Flow: '
        f'[green]{args.flow}[/green] to {args.replicas} replicas'
    )
    await CloudFlow(flow_id=args.flow).scale(
        executor=args.executor, replicas=args.replicas
    )


@asyncify
async def recreate(args):
    from rich import print

    if Resources.Deployment in args.jc_cli:
        print(f'Recreating Deployment: [green]{args.deployment}[/green]')
        await CloudDeployment(deployment_id=args.deployment).recreate()
        return

    print(f'Recreating deleted Flow [green]{args.flow}[/green]')
    await CloudFlow(flow_id=args.flow).recreate()


@asyncify
async def logs(args):
    from rich import print
    from rich import box
    from rich.console import Console
    from rich.syntax import Syntax
    from rich.table import Table

    from .helper import add_table_row_fn, center_align

    _t = Table(
        'Attribute',
        'Value',
        show_header=False,
        box=box.ROUNDED,
        show_lines=True,
    )
    console = Console()
    if Resources.Flow in args.jc_cli or Resources.Deployment in args.jc_cli:

        if Resources.Flow in args.jc_cli:
            name = 'gateway' if args.gateway else f'executor {args.executor}'
            print(
                f'Fetching the logs for {name} of the Flow: [green]{args.flow}[/green]'
            )

            if args.gateway:
                logs = await CloudFlow(flow_id=args.flow).logs()
            else:
                logs = await CloudFlow(flow_id=args.flow).logs(args.executor)

        if Resources.Deployment in args.jc_cli:
            print(f'Fetching the logs for Deployment: [green]{args.deployment}[/green]')
            logs = await CloudDeployment(deployment_id=args.deployment).logs()

        for pod, pod_logs in logs.items():
            with console.status(
                f'[bold]Displaying logs of pod [green]{pod}[/green]...'
            ):
                _pod_id_row = add_table_row_fn(_t, 'POD_ID', center_align(pod))

                _pod_logs_lines = '\n'.join(pod_logs.split('\n'))
                _pod_logs_row = add_table_row_fn(
                    _t,
                    'Logs',
                    Syntax(
                        _pod_logs_lines,
                        lexer='vctreestatus',
                        line_numbers=1,
                        code_width=90,
                    ),
                )

                for fn in [_pod_id_row, _pod_logs_row]:
                    fn()
                console.print(_t)
    else:
        logs = await CloudFlow(flow_id=args.flow).job_logs(args.name)
        with console.status(
            f'[bold]Displaying logs of job [green]{args.name}[/green]...'
        ):
            _job_id_row = add_table_row_fn(_t, 'JOB_NAME', center_align(args.name))
            _job_logs_lines = '\n'.join(logs.split('\n'))
            _job_logs_row = add_table_row_fn(
                _t,
                'Logs',
                Syntax(
                    _job_logs_lines,
                    lexer='vctreestatus',
                    line_numbers=1,
                    code_width=90,
                ),
            )
            for fn in [_job_id_row, _job_logs_row]:
                fn()
            console.print(_t)


@asyncify
async def create(args):
    from rich import print

    if Resources.Job in args.jc_cli:
        await CloudFlow(flow_id=args.flow).create_job(
            args.name,
            args.image,
            args.entrypoint,
            args.timeout,
            args.backofflimit,
            args.secrets,
        )
    else:
        await CloudFlow(flow_id=args.flow, path=args.path).create_secret(
            args.name, args.from_literal, args.update
        )
    print(f'Successfully created {args.jc_cli} [green]{args.name}[/green].')


@asyncify
async def get(args):
    await _display_resources(args)
