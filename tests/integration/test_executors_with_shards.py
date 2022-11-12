import os

import pytest
from jina import Client

from jcloud.flow import CloudFlow

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.skip('unskip once normalization is implemented')
def test_project_with_shards():
    with CloudFlow(
        path=os.path.join(cur_dir, 'projects', 'executors_with_shards'),
        name='executors_with_shards',
    ) as flow:
        shard_0_counter = shard_1_counter = 0
        for _ in range(5):
            da = Client(host=flow.gateway).post(on='/', inputs=[])
            shard_id = da[0].text

            if shard_id == "0":
                shard_0_counter += 1
            elif shard_id == "1":
                shard_1_counter += 1
            else:
                assert False, "Unexpected shard encountered."

        # Both shard-0 and shard-1 should be used at least once.
        assert shard_0_counter > 0 and shard_0_counter > 0
