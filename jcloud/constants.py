from enum import Enum


WOLF_API = 'https://api.wolf.jina.ai/dev/flows'
LOGSTREAM_API = 'wss://logs.wolf.jina.ai/dev'
ARTIFACT_API = 'https://apihubble.jina.ai/v2/rpc/artifact.upload'


class Status(str, Enum):
    SUBMITTED = 'SUBMITTED'
    NORMALIZING = 'NORMALIZING'
    NORMALIZED = 'NORMALIZED'
    STARTING = 'STARTING'
    FAILED = 'FAILED'
    ALIVE = 'ALIVE'
    UPDATING = 'UPDATING'
    DELETING = 'DELETING'
    DELETED = 'DELETED'

    @property
    def streamable(self) -> bool:
        return self in (Status.ALIVE, Status.UPDATING, Status.DELETING)

    @property
    def alive(self) -> bool:
        return self == Status.ALIVE

    @property
    def deleted(self) -> bool:
        return self == Status.DELETED
