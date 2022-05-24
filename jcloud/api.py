import asyncio
import json
from functools import wraps

from .flow import CloudFlow


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
            for k, v in _result.items():
                if k == 'yaml' and v is not None:
                    v = Syntax(
                        v, 'yaml', theme='monokai', line_numbers=True, code_width=40
                    )
                elif k == 'envs' and v:
                    v = JSON(json.dumps(v))
                else:
                    v = str(v)
                _t.add_row(k, v)
            console.print(_t)


@asyncify
async def list(args):
    from datetime import datetime, timezone

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

    _t = Table('ID', 'Status', 'Gateway', 'Created', box=box.ROUNDED, highlight=True)

    console = Console(highlighter=CustomHighlighter())
    _status = args.status
    with console.status(
        f'[bold]Listing flows with status [green]{_status}[/green] ...'
        if _status is not None or _status != 'ALL'
        else '[bold] Listing all Flows'
    ):
        _result = await CloudFlow().list_all(status=args.status)
        if _result:
            for k in _result:
                _t.add_row(
                    k['id'].split('-')[-1],
                    k['status'],
                    k['gateway'],
                    cleanup(k['ctime']),
                )
            console.print(_t)


@asyncify
async def remove(args):
    from rich import print

    await CloudFlow(flow_id=args.flow).__aexit__()
    print(f'Successfully removed Flow [green]{args.flow}[/green]')


@asyncify
async def logs(args):
    from .flow import pb_task, pbar

    with pbar:
        pbar.start_task(pb_task)
        pbar.update(
            pb_task,
            total=1,
            description=f'Press Ctrl-C to quit',
            title=f'Live streaming from {args.flow}',
        )
        _params = {'flow_id': args.flow}
        if args.executor is not None:
            _params['executor'] = args.executor
        await CloudFlow.logstream(_params)


@asyncify
async def login(args):
    from .auth import Auth

    await Auth.login()


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
    from .auth import Survey

    Survey().ask(-1)
