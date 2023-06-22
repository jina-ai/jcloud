import os
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

JCLOUD_API = os.getenv('JCLOUD_API', 'https://api-v2.wolf.jina.ai/')
FLOWS_API = os.path.join(JCLOUD_API, 'flows')
JOBS_API = os.path.join(JCLOUD_API, 'jobs')
SECRETS_API = os.path.join(JCLOUD_API, 'secrets')
DASHBOARD_URL_MARKDOWN = "[https://cloud.jina.ai/](https://cloud.jina.ai/user/flows?action=detail&id={flow_id}&tab=logs)"
DASHBOARD_URL_LINK = "[link=https://cloud.jina.ai/user/flows?action=detail&id={flow_id}&tab=logs]https://cloud.jina.ai/[/link]"


class Phase(str, Enum):
    Empty = ''
    Pending = 'Pending'
    Starting = 'Starting'
    Serving = 'Serving'
    Failed = 'Failed'
    Updating = 'Updating'
    Deleted = 'Deleted'
    Paused = 'Paused'


class CONSTANTS:
    DEFAULT_FLOW_FILENAME = 'flow.yml'
    DEFAULT_ENV_FILENAME = '.env'
    NORMED_FLOWS_DIR = Path('/tmp/flows')


class CustomAction(str, Enum):
    NoAction = ''
    Restart = 'restart'
    Pause = 'pause'
    Resume = 'resume'
    Scale = 'scale'
    Recreate = 'recreate'


class Resources(str, Enum):
    Flow = 'flow'
    Job = 'job'
    Secret = 'secret'


def get_phase_from_response(response: Dict) -> Optional[Phase]:
    return Phase(response.get('status', {}).get('phase'))
