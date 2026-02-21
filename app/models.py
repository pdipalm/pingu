import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class IcmpTarget:
    id: uuid.UUID
    name: str
    host: str
    interval_seconds: int
    timeout_ms: int


@dataclass(frozen=True)
class HttpTarget:
    id: uuid.UUID
    name: str
    url: str
    interval_seconds: int
    timeout_ms: int

