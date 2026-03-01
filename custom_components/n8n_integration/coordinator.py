"""DataUpdateCoordinator for n8n_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    N8nIntegrationApiClientAuthenticationError,
    N8nIntegrationApiClientError,
)

if TYPE_CHECKING:
    from .data import N8nIntegrationConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class N8nDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: N8nIntegrationConfigEntry

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            # Fetch workflows from the API
            return await self.config_entry.runtime_data.client.async_get_workflows()
        except N8nIntegrationApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except N8nIntegrationApiClientError as exception:
            raise UpdateFailed(exception) from exception
