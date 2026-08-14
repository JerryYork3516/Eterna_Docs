"""Synthetic, offline-only helpers for MVP Collector tests."""

from __future__ import annotations

from types import MappingProxyType

from collectors.transport import TransportResponse
from pipeline.config import SourceConfigEntry, validate_source_config
from pipeline.registry import RegistryEntry, SourceRegistry


class StaticTransport:
    def __init__(
        self,
        body: bytes = b"",
        *,
        final_url: str,
        content_type: str,
        error: Exception | None = None,
    ) -> None:
        self.body = body
        self.final_url = final_url
        self.content_type = content_type
        self.error = error
        self.calls: list[tuple[str, tuple[str, ...], str]] = []

    def get(
        self,
        url: str,
        *,
        accepted_content_types: tuple[str, ...],
        accept: str,
    ) -> TransportResponse:
        self.calls.append((url, accepted_content_types, accept))
        if self.error is not None:
            raise self.error
        return TransportResponse(
            body=self.body,
            final_url=self.final_url,
            status_code=200,
            content_type=self.content_type,
        )


def configured_source(
    *,
    name: str,
    region: str,
    collector_type: str,
    url: str,
    enabled: bool = True,
    parameters: dict[str, object] | None = None,
    source_type: str = "Official",
) -> tuple[SourceConfigEntry, SourceRegistry]:
    registry = SourceRegistry(
        entries=MappingProxyType(
            {
                name: RegistryEntry(
                    name=name,
                    source_type=source_type,
                    region=region,
                    platform="Synthetic public test source",
                    urls=(url,),
                    priority="P0" if source_type == "Official" else "P2",
                    credibility="High" if source_type == "Official" else "Medium",
                    fact_citation="Yes" if source_type == "Official" else "Conditional",
                    eterna_tags=("Agent", "AI Coding"),
                )
            }
        )
    )
    payload = {
        "schema_version": 1,
        "region": region,
        "sources": [
            {
                "registry_ref": name,
                "region": region,
                "collector_type": collector_type,
                "url": url,
                "enabled": enabled,
                "parameters": parameters or {},
            }
        ],
    }
    config = validate_source_config(payload, region, registry)
    return config.sources[0], registry
