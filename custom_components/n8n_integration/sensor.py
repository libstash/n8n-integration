"""Sensor platform for n8n_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import LOGGER
from .entity import N8nIntegrationEntity

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant, ServiceResponse
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import N8nDataUpdateCoordinator
    from .data import N8nIntegrationConfigEntry
    from .models import Workflow, WorkflowNode


WEBHOOK_NODE = "n8n-nodes-base.webhook"
TRIGGER_NODES = {WEBHOOK_NODE, "n8n-nodes-base.formTrigger"}

SERVICE_TRIGGER_WEBHOOK = "trigger_webhook"
ATTR_PAYLOAD = "payload"
ATTR_METHOD = "method"
HTTP_METHODS = ["DELETE", "GET", "HEAD", "PATCH", "POST", "PUT"]


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: N8nIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator

    workflows: list[Workflow] = coordinator.data.get("data", [])

    entities: list[N8nIntegrationTriggerSensor] = [
        N8nIntegrationTriggerSensor(
            coordinator=coordinator,
            node=node,
            workflow=workflow,
        )
        for workflow in workflows
        for node in workflow.get("nodes", [])
        if node.get("type") in TRIGGER_NODES
    ]

    async_add_entities(entities)

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_TRIGGER_WEBHOOK,
        {
            vol.Optional(ATTR_PAYLOAD): vol.Schema({cv.string: object}),
            vol.Optional(ATTR_METHOD): vol.All(vol.Upper, vol.In(HTTP_METHODS)),
        },
        "async_handle_trigger_webhook",
        supports_response=SupportsResponse.OPTIONAL,
    )


class N8nIntegrationTriggerSensor(N8nIntegrationEntity, SensorEntity):
    """n8n_integration Sensor class."""

    entity_description = SensorEntityDescription(
        key="n8n_workflow",
        device_class=SensorDeviceClass.TIMESTAMP,
    )

    def __init__(
        self,
        coordinator: N8nDataUpdateCoordinator,
        node: WorkflowNode,
        workflow: Workflow,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)

        self._workflow: Workflow = workflow
        self._node: WorkflowNode = node

        workflow_id = workflow.get("id")
        workflow_name = workflow.get("name")
        node_id = node.get("id")
        node_name = node.get("name")

        self._attr_unique_id = f"{self._attr_unique_id}-{workflow_id}-{node_id}-sensor"
        self._attr_icon = "mdi:transit-connection-horizontal"
        self._attr_name = f"{workflow_name}: {node_name}"

        self._last_triggered_at: str | None = None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        api_client = self.coordinator.config_entry.runtime_data.client
        url: str | None = getattr(api_client, "url", None)
        node_type: str | None = self._node.get("type")

        attrs: dict[str, Any] = {
            "workflow_id": self._workflow.get("id"),
            "workflow_name": self._workflow.get("name"),
            "n8n_url": url,
            "type": node_type,
        }

        if node_type == "n8n-nodes-base.formTrigger":
            webhook_id: str | None = self._node.get("webhookId")
            if webhook_id and url:
                attrs["form_url"] = f"{url}/form/{webhook_id}"
            else:
                LOGGER.warning(
                    "Form trigger node %s has no webhookId or URL",
                    self._node.get("id"),
                )

        return attrs

    async def async_handle_trigger_webhook(
        self,
        payload: dict[str, Any] | None = None,
        method: str | None = None,
    ) -> ServiceResponse:
        """Handle the trigger_webhook action with an optional payload and method."""
        if self._node.get("type") != WEBHOOK_NODE:
            msg = f"{self.entity_id} is not a webhook trigger and cannot be triggered"
            raise ServiceValidationError(msg)

        options = {}
        if self._last_triggered_at is not None:
            options["_last_triggered_at"] = self._last_triggered_at

        client = self.coordinator.config_entry.runtime_data.client

        result = await client.async_trigger_webhook(
            self._node, options, payload, method
        )

        self._last_triggered_at = dt_util.utcnow().isoformat()
        await self.coordinator.async_request_refresh()
        return {"response": result}

    @property
    def native_value(self) -> datetime | None:
        """Return the native value of the sensor."""
        updated_at = self._workflow.get("updatedAt")
        if updated_at:
            return dt_util.parse_datetime(updated_at)
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        workflow_id: str = self._workflow.get("id") or ""
        workflow_name: str | None = self._workflow.get("name")

        return DeviceInfo(
            identifiers={("n8n_integration", workflow_id)},
            name=workflow_name,
            manufacturer="n8n",
        )
