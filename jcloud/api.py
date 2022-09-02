import asyncio
import json
import os
from functools import wraps

from .constants import Status
from .flow import CloudFlow, _terminate_flow_simplified
from .helper import prepare_flow_model_for_render


def asyncify(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@asyncify
async def deploy(args):
    return await CloudFlow(
        path=args.path,
        name=args.name,
        workspace_id=args.workspace,
        env_file=args.env_file,
    ).__aenter__()


@asyncify
async def status(args):
    from rich import box
    from rich.console import Console
    from rich.json import JSON
    from rich.syntax import Syntax
    from rich.table import Table

    from .helper import CustomHighlighter

    _t = Table('Attribute', 'Value', show_header=False, box=box.ROUNDED, highlight=True)

    console = Console(highlighter=CustomHighlighter())
    with console.status(f'[bold]Fetching status of {args.flow}...'):
        _result = await CloudFlow(flow_id=args.flow).status
        if not _result:
            console.print(
                f'[red]Something went wrong while fetching the details for {args.flow} ![/red]. Please retry after sometime.'
            )
        else:
            prepare_flow_model_for_render(_result)
            for k, v in _result.items():
                if k == 'yaml' and v is not None:
                    v = Syntax(
                        v, 'yaml', theme='monokai', line_numbers=True, code_width=40
                    )
                elif k in ('envs', 'endpoints') and v:
                    v = JSON(json.dumps(v))
                else:
                    v = str(v)
                _t.add_row(k, v)
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
        if _result:
            for k in _result:
                if k['gateway'] is None and k.get('endpoints') is not None:
                    _endpoint = json.dumps(k['endpoints'], indent=2, sort_keys=True)
                else:
                    _endpoint = k['gateway']
                _t.add_row(
                    k['id'].split('-')[-1],
                    k['status'],
                    _endpoint,
                    cleanup(k['ctime']),
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

        _raw_list = await _list_by_status(Status.ALIVE.value)
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
