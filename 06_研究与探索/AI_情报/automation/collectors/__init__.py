"""Offline-testable MVP Collector Layer without Normalizer responsibilities."""

from collectors.base import (
    CollectionBatch,
    CollectionError,
    CollectionErrorKind,
    CollectionItemError,
    RawCollectorRecord,
)
from collectors.dispatch import collect_configured_source
from collectors.transport import HttpTransport, TransportResponse, TransportSettings


__all__ = (
    "CollectionBatch",
    "CollectionError",
    "CollectionErrorKind",
    "CollectionItemError",
    "HttpTransport",
    "RawCollectorRecord",
    "TransportResponse",
    "TransportSettings",
    "collect_configured_source",
)
