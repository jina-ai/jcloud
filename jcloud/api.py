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
    await CloudFlow(filepath=args.path, name=args.name, workspace_id=args.workspace).__aenter__()


@asyncify
async def status(args):
    print(json.dumps(await CloudFlow(flow_id=args.flow).status, indent=2))


@asyncify
async def remove(args):
    await CloudFlow(flow_id=args.flow).__aexit__()


@asyncify
async def logs(args):
    await CloudFlow.logstream(params={'flow_id': args.flow})
