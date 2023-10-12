from jina import Client, Document, DocumentArray

from jcloud.flow import CloudFlow
from jcloud.deployment import CloudDeployment
from jcloud.constants import Phase
from ..integration.flow import FlowAlive

import time


def get_condition_from_status(status, cond_type=FlowAlive):
    try:
        sts = status["status"]
        conds = sts["conditions"]
        for c in conds:
            if c["type"] == cond_type:
                return c
    except KeyError:
        return None


def get_last_transition_time(
    res: CloudFlow | CloudDeployment,
    condition_type,
) -> str:
    try:
        status = res._loop.run_until_complete(res.status)
        cnd = get_condition_from_status(status, condition_type)
        if cnd:
            return cnd['lastTransitionTime']
    except KeyError:
        pass

    return ''


def eventually_reaches_phase(
    res: CloudFlow | CloudDeployment,
    phase=Phase.Serving,
    num_of_retries=12,
    interval=30,
) -> bool:

    for i in range(num_of_retries):
        time.sleep(interval)
        status = res._loop.run_until_complete(res.status)
        try:
            sts = status['status']
            p = sts['phase']
            if p == phase:
                return True
        except KeyError:
            pass

    return False


def eventually_condition_gets_updated(
    res: CloudFlow | CloudDeployment,
    condition_type,
    condition_timestamp,
    num_of_retries=6,
    interval=4,
) -> bool:
    for i in range(num_of_retries):
        nltt = get_last_transition_time(res, condition_type)
        if nltt > condition_timestamp:
            return True

        time.sleep(interval)

    return False


def eventually_serve_requests(
    endpoint: str,
    num_of_retries=12,
    interval=3,
) -> bool:
    for _ in range(num_of_retries):
        time.sleep(interval)
        try:
            da = Client(host=endpoint).post(
                on='/',
                inputs=DocumentArray(Document(text=f'text-{i}') for i in range(50)),
            )
            if len(da.texts) == 50:
                return True
        except (ValueError, ConnectionError) as e:
            print(e, ". retrying")

    return False
