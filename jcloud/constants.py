import os
from enum import Enum
from typing import Dict, Optional

JCLOUD_API = os.getenv('JCLOUD_API', 'https://api.wolf.jina.ai/dev/')
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

    @property
    def alive(self) -> bool:
        return self == Phase.Serving

    @property
    def deleted(self) -> bool:
        return self == Phase.Deleted


def get_phase_from_response(response: Dict) -> Optional[Phase]:
    return Phase(response.get('status', {}).get('phase'))
