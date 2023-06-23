import os
import asyncio

from jcloud.flow import CloudFlow
from jcloud.constants import Resources

from http import HTTPStatus

flows_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'basic', 'flows'
)
flow_file = 'http-flow.yml'


def test_jobs():
    with CloudFlow(path=os.path.join(flows_dir, flow_file)) as flow:

        job_response = asyncio.run(
            flow.create_job(
                'test-job', 'docker://jinaai/jina:3.18-standard', 600, 5, 'jina -v'
            )
        )
        assert 'name' in job_response
        assert 'status' in job_response

        job_logs = ''
        while len(job_logs) == 0:
            job_logs = asyncio.run(flow.job_logs('test-job'))
        assert '3.18.0' in job_logs

        job = asyncio.run(flow.get_resource(Resources.Job, 'test-job'))
        assert job['name'] == 'test-job'
        asyncio.run(flow.delete_resource(Resources.Job, 'test-job'))
