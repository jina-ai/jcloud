import asyncio
import json
from functools import wraps

import click

from .flow import WolfFlow


def asyncify(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.group()
def wolf():
    pass


@wolf.command()
@click.option(
    '--yaml',
    help='Pass the Flow yaml filepath',
    required=True,
    type=click.Path(exists=True),
)
@click.option(
    '--name',
    help='Pass a custom name to assign to the Flow',
    default=None,
)
@click.option(
    '--workspace',
    help='Pass an already existing workspace id for the Flow',
    default=None,
)
@asyncify
async def deploy(yaml, name, workspace):
    await WolfFlow(filepath=yaml, name=name, workspace=workspace).__aenter__()


@wolf.command()
@click.option('--id', help='Pass the Flow ID')
@asyncify
async def fetch(id):
    print(json.dumps(await WolfFlow(flow_id=id).fetch(flow_id=id), indent=2))


@wolf.command()
@click.option('--id', help='Pass the Flow ID')
@asyncify
async def terminate(id):
    await WolfFlow(flow_id=id).__aexit__()


@wolf.command()
@click.option('--id', help='Pass the Flow ID')
@asyncify
async def logs(id):
    await WolfFlow.logstream(params={'flow_id': id})


if __name__ == '__main__':
    wolf()
