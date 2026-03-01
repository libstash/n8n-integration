"""Adds config flow for Blueprint."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_TOKEN, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from slugify import slugify

from .api import (
    N8nIntegrationApiClient,
    N8nIntegrationApiClientAuthenticationError,
    N8nIntegrationApiClientCommunicationError,
    N8nIntegrationApiClientError,
)
from .const import DOMAIN, LOGGER


class N8nFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for n8n."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    url=user_input[CONF_URL],
                    api_token=user_input[CONF_API_TOKEN],
                )
            except N8nIntegrationApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except N8nIntegrationApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except N8nIntegrationApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    ## Do NOT use this in production code
                    ## The unique_id should never be something that can change
                    ## https://developers.home-assistant.io/docs/config_entries_config_flow_handler#unique-ids
                    unique_id=slugify(user_input[CONF_URL])
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_URL],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_URL,
                        default=(user_input or {}).get(CONF_URL, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_API_TOKEN): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_credentials(self, url: str, api_token: str) -> None:
        """Validate credentials."""
        client = N8nIntegrationApiClient(
            url=url,
            api_token=api_token,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_workflows()

    @staticmethod
    @callback
    def async_get_options_flow(
        _config_entry: config_entries.ConfigEntry,
    ) -> N8nOptionsFlowHandler:
        """Get the options flow for this handler."""
        return N8nOptionsFlowHandler()


class N8nOptionsFlowHandler(config_entries.OptionsFlowWithReload):
    """Handle options flow for n8n."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage the integration options."""

        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    url=user_input[CONF_URL],
                    api_token=user_input[CONF_API_TOKEN],
                )
            except N8nIntegrationApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except N8nIntegrationApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except N8nIntegrationApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                data = {
                    **self.config_entry.data,
                    CONF_URL: user_input[CONF_URL],
                    CONF_API_TOKEN: user_input[CONF_API_TOKEN],
                }
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title=user_input[CONF_URL],
                    data=data,
                )

                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_URL,
                        default=(user_input or self.config_entry.options).get(
                            CONF_URL,
                            self.config_entry.data.get(CONF_URL, vol.UNDEFINED),
                        ),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_API_TOKEN,
                        default=(user_input or self.config_entry.options).get(
                            CONF_API_TOKEN,
                            self.config_entry.data.get(CONF_API_TOKEN, vol.UNDEFINED),
                        ),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_credentials(self, url: str, api_token: str) -> None:
        """Validate credentials."""
        client = N8nIntegrationApiClient(
            url=url,
            api_token=api_token,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_workflows()
