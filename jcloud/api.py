import asyncio
import json
import os
from functools import wraps

from .constants import Phase
from .flow import CloudFlow, _terminate_flow_simplified
from .helper import (
    get_endpoints_from_response,
    get_phase_from_response,
    jsonify,
    yamlify,
)


def asyncify(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@asyncify
async def deploy(args):
    return await CloudFlow(path=args.path).__aenter__()


@asyncify
async def status(args):
    from rich import box
    from rich.align import Align
    from rich.console import Console
    from rich.json import JSON
    from rich.syntax import Syntax
    from rich.table import Table

    from .helper import CustomHighlighter

    _t = Table('Attribute', 'Value', show_header=False, box=box.ROUNDED, highlight=True)

    def _add_row_fn(key, value):
        return lambda: _t.add_row(Align(f'[bold]{key}', vertical='middle'), value)

    console = Console(highlighter=CustomHighlighter())
    with console.status(f'[bold]Fetching status of {args.flow}...'):
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
                            _phase_row = _add_row_fn(
                                _k, Align(f'[bold]{_v}[/bold]', align='center')
                            )

                        elif _k in ('endpoints', 'dashboards') and _v:
                            # Show Endpoints and Dashboards
                            _other_rows.append(_add_row_fn(_k, JSON(jsonify(_v))))

                        elif _k == 'conditions' and args.verbose:
                            # Show Conditions only if verbose
                            _other_rows.append(_add_row_fn(_k, JSON(jsonify(_v))))

                        elif _k == 'version' and args.verbose:
                            # Show Jina version only if verbose
                            _other_rows.append(_add_row_fn("jina version", _v))

                elif k == 'spec' and v is not None:
                    v = Syntax(
                        yamlify(v),
                        'yaml',
                        theme='monokai',
                        line_numbers=1,
                        code_width=60,
                    )
                    _other_rows.append(_add_row_fn(k, v))

                elif k == 'error' and v:
                    _other_rows.append(_add_row_fn(k, f'[red]{v}[red]'))

            for fn in [_id_row, _phase_row, *_other_rows]:
                fn()
            console.print(_t)


async def _list_by_status(status):
    from datetime import datetime

    from rich import box
    from rich.console import Console
    from rich.table import Table

    from .helper import CustomHighlighter

    def cleanup(dt) -> str:
        try:
            return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f%z').strftime(
                '%d-%b-%Y %H:%M'
            )
        except:
            return dt

    _t = Table(
        'ID', 'Status', 'Endpoint(s)', 'Created (UTC)', box=box.ROUNDED, highlight=True
    )

    console = Console(highlighter=CustomHighlighter())
    with console.status(
        f'[bold]Listing flows with status [green]{status}[/green] ...'
        if status is not None or status != 'ALL'
        else '[bold] Listing all Flows'
    ):
        _result = await CloudFlow().list_all(status=status)
        if _result and 'flows' in _result:
            for flow in _result['flows']:
                _t.add_row(
                    flow['id'],
                    get_phase_from_response(flow),
                    get_endpoints_from_response(flow),
                    cleanup(flow['ctime']),
                )
            console.print(_t)
        return _result


@asyncify
async def list(args):
    await _list_by_status(args.status)


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

        _raw_list = await _list_by_status(Phase.ALIVE.value)
        print('Above are the flows about to be deleted.\n')

        if 'JCLOUD_NO_INTERACTIVE' not in os.environ:
            confirm_deleting_again = Confirm.ask(
                '[red]Are you sure you want to delete them?[/red]', default=True
            )
            if not confirm_deleting_again:
                print('[cyan]No worries. Exiting...[/cyan]')
                return

        flow_id_list = [flow['id'].split('-')[-1] for flow in _raw_list]

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


def logs(args):
    from rich import print

    print("[red]'jc logs' command will be deprecated soon![/red]")
    print(
        f"Please visit https://dashboard.wolf.jina.ai/flow/{args.flow} for Flow logs instead.\nThis link can also be found at the bottom of the output from 'jc status'."
    )


def login(args):
    import hubble

    hubble.login()


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
