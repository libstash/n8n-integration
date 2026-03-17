"""n8n API Client."""

from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Any

import aiohttp
import async_timeout

if TYPE_CHECKING:
    from .models import WorkflowNode


class N8nIntegrationApiClientError(Exception):
    """Exception to indicate a general API error."""


class N8nIntegrationApiClientCommunicationError(
    N8nIntegrationApiClientError,
):
    """Exception to indicate a communication error."""


class N8nIntegrationApiClientAuthenticationError(
    N8nIntegrationApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise N8nIntegrationApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class N8nIntegrationApiClient:
    """n8n API Client."""

    def __init__(
        self,
        url: str,
        api_token: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """n8n API Client."""
        self._url = url.rstrip("/")
        self._api_token = api_token
        self._session = session

    async def async_get_workflows(self) -> Any:
        """Get workflows from the API."""
        return await self._api_wrapper(
            method="get",
            url=f"{self._url}/api/v1/workflows?active=true",
            headers={"X-N8N-API-KEY": self._api_token},
        )

    async def async_get_workflow(self, workflow_id: str) -> Any:
        """Get workflow from the API."""
        return await self._api_wrapper(
            method="get",
            url=f"{self._url}/api/v1/workflows/{workflow_id}",
            headers={"X-N8N-API-KEY": self._api_token},
        )

    async def async_trigger_webhook(
        self,
        webhook_node: WorkflowNode,
        options: dict[str, Any],
    ) -> Any:
        """Trigger the n8n webhook node using its parameters."""
        parameters = webhook_node.get("parameters", {})
        method = parameters.get("httpMethod", "GET")
        path = parameters.get("path")
        if not method or not path:
            msg = (
                "Webhook node is missing required parameters: "
                f"method={method}, path={path}"
            )
            raise N8nIntegrationApiClientError(msg)
        method = method.lower()
        url = f"{self._url}/webhook/{path}"
        headers = {}

        params = {}
        if last_triggered := options.get("_last_triggered_at"):
            params["_last_triggered_at"] = str(last_triggered)

        return await self._api_wrapper(
            method=method,
            url=url,
            headers=headers,
            params=params,
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
        params: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise N8nIntegrationApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise N8nIntegrationApiClientCommunicationError(
                msg,
            ) from exception
        except N8nIntegrationApiClientAuthenticationError:
            # Re-raise so config flow can catch it
            raise
        except N8nIntegrationApiClientCommunicationError:
            # Re-raise so config flow can catch it
            raise
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise N8nIntegrationApiClientError(
                msg,
            ) from exception

    @property
    def url(self) -> str:
        """Get client URL."""
        return self._url
