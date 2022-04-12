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
    await CloudFlow(
        path=args.path, name=args.name, workspace=args.workspace
    ).__aenter__()


@asyncify
async def status(args):
    print(json.dumps(await CloudFlow(flow_id=args.flow_id).status, indent=2))


@asyncify
async def remove(args):
    await CloudFlow(flow_id=args.flow_id).__aexit__()


@asyncify
async def logs(args):
    await CloudFlow.logstream(params={'flow_id': args.flow_id})
