import os

from pathlib import Path
from enum import Enum
from typing import Dict, Optional

JCLOUD_API = os.getenv('JCLOUD_API', 'https://api-v2.wolf.jina.ai/')
FLOWS_API = os.path.join(JCLOUD_API, 'flows')
ARTIFACT_API = 'https://api.hubble.jina.ai/v2/rpc/artifact.upload'


class Phase(str, Enum):
    Empty = ''
    Pending = 'Pending'
    Starting = 'Starting'
    Serving = 'Serving'
    Failed = 'Failed'
    Updating = 'Updating'
    Deleted = 'Deleted'


class CONSTANTS:
    DEFAULT_FLOW_FILENAME = 'flow.yml'
    DEFAULT_ENV_FILENAME = '.env'
    NORMED_FLOWS_DIR = Path('/tmp/flows')


def get_phase_from_response(response: Dict) -> Optional[Phase]:
    return Phase(response.get('status', {}).get('phase'))
