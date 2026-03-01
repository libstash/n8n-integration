"""Custom types for n8n_integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import N8nIntegrationApiClient
    from .coordinator import N8nDataUpdateCoordinator


type N8nIntegrationConfigEntry = ConfigEntry[N8nIntegrationData]


@dataclass
class N8nIntegrationData:
    """Data for the n8n integration."""

    client: N8nIntegrationApiClient
    coordinator: N8nDataUpdateCoordinator
    integration: Integration
