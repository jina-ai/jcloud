from jcloud.flow import CloudFlow
from jcloud.deployment import CloudDeployment
from jcloud.constants import Phase
from ..integration.flow import FlowAlive


def get_condition_from_status(status, cond_type=FlowAlive):
    try:
        sts = status["status"]
        conds = sts["conditions"]
        for c in conds:
            if c["type"] == cond_type:
                return c
    except KeyError:
        return None


def eventually_reaches_phase(
    res: CloudFlow | CloudDeployment, phase=Phase.Serving, num_of_retries=3
) -> bool:
    for i in range(num_of_retries):
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
    num_of_retries=3,
) -> bool:
    for i in range(num_of_retries):
        status = res._loop.run_until_complete(res.status)
        cnd = get_condition_from_status(status, condition_type)
        if not cnd:
            continue
        nltt = cnd["lastTransitionTime"]
        if nltt > condition_timestamp:
            return True

    return False
