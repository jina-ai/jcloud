import asyncio
import os
from functools import wraps

from .constants import Phase
from .flow import CloudFlow, _terminate_flow_simplified
from .helper import (
    cleanup_dt,
    get_phase_from_response,
    get_str_endpoints_from_response,
    jsonify,
    yamlify,
)
from .normalize import flow_normalize


def asyncify(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@asyncify
async def deploy(args):
    return await CloudFlow(path=args.path).__aenter__()


def normalize(args):
    flow_normalize(path=args.path, verbose=args.verbose, output_path=args.output)


@asyncify
async def status(args):
    from rich import box
    from rich.align import Align
    from rich.console import Console
    from rich.json import JSON
    from rich.syntax import Syntax
    from rich.table import Table

    from .helper import CustomHighlighter

    _t = Table(
        'Attribute',
        'Value',
        show_header=False,
        box=box.ROUNDED,
        highlight=True,
        show_lines=True,
    )

    def _add_row_fn(key, value):
        return lambda: _t.add_row(Align(f'[bold]{key}', vertical='middle'), value)

    def _center_align(value):
        return Align(f'[bold]{value}[/bold]', align='center')

    console = Console(highlighter=CustomHighlighter())
    with console.status(f'[bold]Fetching status of [green]{args.flow}[/green] ...'):
        _result = await CloudFlow(flow_id=args.flow).status
        if not _result:
            console.print(
                f'[red]Something went wrong while fetching the details for {args.flow} ![/red]. Please retry after sometime.'
            )
        else:
            _other_rows = []
            for k, v in _result.items():
                if k == 'id':
                    _id_row = _add_row_fn(
                        'ID', Align(f'[bold]{v}[/bold]', align='center')
                    )

                elif k == 'status':
                    for _k, _v in v.items():
                        if _k == 'phase':
                            # Show Phase
                            _phase_row = _add_row_fn('Phase', _center_align(_v))

                        elif _k == 'endpoints' and _v:
                            # Show Endpoints and Dashboards
                            _other_rows.append(
                                _add_row_fn("Endpoint(s)", JSON(jsonify(_v)))
                            )

                        elif _k == 'dashboards' and _v:
                            # Show Dashboard
                            if _v.get('grafana'):
                                _other_rows.append(
                                    _add_row_fn(
                                        'Grafana Dashboard',
                                        _center_align(_v.get('grafana')),
                                    )
                                )
                            else:
                                _other_rows.append(
                                    _add_row_fn(
                                        'Dashboards',
                                        _v,
                                    )
                                )

                        elif _k == 'conditions' and args.verbose:
                            # Show Conditions only if verbose
                            _other_rows.append(
                                _add_row_fn('Details', JSON(jsonify(_v)))
                            )

                        elif _k == 'version' and args.verbose:
                            # Show Jina version only if verbose
                            _other_rows.append(
                                _add_row_fn("Jina Version", _center_align(_v))
                            )

                elif k == 'spec' and v is not None:
                    v = Syntax(
                        yamlify(v),
                        'yaml',
                        theme='monokai',
                        line_numbers=1,
                        code_width=60,
                    )
                    _other_rows.append(_add_row_fn('Spec', v))

                elif k == 'error' and v:
                    _other_rows.append(_add_row_fn(k, f'[red]{v}[red]'))

                elif k in ('ctime', 'utime'):
                    _other_rows.append(
                        _add_row_fn(
                            'Created' if k == 'ctime' else 'Updated',
                            _center_align(cleanup_dt(v)),
                        ),
                    )

            for fn in [_id_row, _phase_row, *_other_rows]:
                fn()
            console.print(_t)


async def _list_by_phase(phase: str, name: str):

    from rich import box
    from rich.console import Console
    from rich.table import Table

    from .helper import CustomHighlighter

    _t = Table(
        'ID', 'Status', 'Endpoint(s)', 'Created', box=box.ROUNDED, highlight=True
    )

    console = Console(highlighter=CustomHighlighter())
    msg = f'[bold]Fetching [green]{phase}[/green] flows'
    if name:
        msg += f' with name [green]{name}[/green]'
    msg += ' ...'

    with console.status(msg):
        _result = await CloudFlow().list_all(phase=phase, name=name)
        if _result and 'flows' in _result:
            for flow in _result['flows']:
                _t.add_row(
                    flow['id'],
                    get_phase_from_response(flow),
                    get_str_endpoints_from_response(flow),
                    cleanup_dt(flow['ctime']),
                )
            console.print(_t)
        return _result


@asyncify
async def list(args):
    await _list_by_phase(args.phase, args.name)


@asyncify
async def remove(args):
    from rich import print
    from rich.prompt import Confirm

    if args.flows == []:
        print('[cyan]Please pass in flow(s) to remove. Exiting...[/cyan]')
        return

    # Case 1: remove single flow, using full progress bar.
    if len(args.flows) == 1 and args.flows != ['all']:
        await CloudFlow(flow_id=args.flows[0]).__aexit__()
        print(f'Successfully removed Flow [green]{args.flows[0]}[/green].')
        return

    # Case 2: remove a list of selected flows, using simplied progress bar.
    if len(args.flows) > 1:
        if 'JCLOUD_NO_INTERACTIVE' not in os.environ:
            confirmation_message_details = '\n'.join(args.flows)
            confirm_deleting_all = Confirm.ask(
                f'Selected flows: \n[red]{confirmation_message_details}\n\nAre you sure you want to delete above flows? [/red]'
            )
            if not confirm_deleting_all:
                print('[cyan]No worries. Exiting...[/cyan]')
                return

        flow_id_list = args.flows

    # Case 3: remove all ALIVE flows.
    else:
        if 'JCLOUD_NO_INTERACTIVE' not in os.environ:
            confirm_deleting_all = Confirm.ask(
                f'[red]Are you sure you want to delete ALL the ALIVE flows that belong to you?[/red]',
                default=True,
            )
            if not confirm_deleting_all:
                print('[cyan]No worries. Exiting...[/cyan]')
                return

        _raw_list = await _list_by_phase(Phase.Serving.value, name='')
        print('Above are the flows about to be deleted.\n')

        if 'JCLOUD_NO_INTERACTIVE' not in os.environ:
            confirm_deleting_again = Confirm.ask(
                '[red]Are you sure you want to delete them?[/red]', default=True
            )
            if not confirm_deleting_again:
                print('[cyan]No worries. Exiting...[/cyan]')
                return

        flow_id_list = [flow['id'] for flow in _raw_list['flows']]

    await _remove_multi(flow_id_list)


async def _remove_multi(flow_id_list):
    from rich import print

    from .helper import get_pbar

    num_flows_to_remove = len(flow_id_list)
    pbar, pb_task = get_pbar(
        '', total=num_flows_to_remove, disable='JCLOUD_NO_PROGRESSBAR' in os.environ
    )

    with pbar:
        pbar.start_task(pb_task)
        pbar.update(
            pb_task,
            description='Starting',
            title=f'Removing {num_flows_to_remove} flows...',
        )

        coros = [_terminate_flow_simplified(flow) for flow in flow_id_list]
        counter = 0
        has_failure_task = False
        for coro in asyncio.as_completed(coros):
            try:
                flow_id = await coro
                counter += 1
                print(f'[red]{flow_id} removed![/red]')
                pbar.update(
                    pb_task,
                    advance=1,
                    description=f'Last flow removed: [red]{flow_id}[/red]. {num_flows_to_remove - counter} flow(s) to go',
                )
            except:
                has_failure_task = True
        await CloudFlow._cancel_pending()

    if has_failure_task:
        print(f'Some flows were not removed properly, please check!')
    else:
        print(f'Successfully removed flows listed above.')


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


def survey(args):
    # ask feedback
    from .survey import Survey

    Survey().ask(-1)


@asyncify
async def update(args):
    from rich import print

    print(f'Updating Flow: [green]{args.flow}[/green]')
    await CloudFlow(flow_id=args.flow, path=args.path).update()


@asyncify
async def restart(args):
    from rich import print

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

    print(f'Pausing Flow: [orange3]{args.flow}[/orange3]')
    await CloudFlow(flow_id=args.flow).pause()


@asyncify
async def resume(args):
    from rich import print

    print(f'Resuming Flow: [green]{args.flow}[/green]')
    await CloudFlow(flow_id=args.flow).resume()


@asyncify
async def scale(args):
    from rich import print

    print(
        f'Scaling Executor: [red]{args.executor}[/red] of the Flow: '
        f'[green]{args.flow}[/green] to {args.replicas} replicas'
    )
    await CloudFlow(flow_id=args.flow).scale(
        executor=args.executor, replicas=args.replicas
    )
