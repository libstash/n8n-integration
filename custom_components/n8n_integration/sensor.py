"""Sensor platform for n8n_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import LOGGER
from .entity import N8nIntegrationEntity

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import N8nDataUpdateCoordinator
    from .data import N8nIntegrationConfigEntry
    from .models import Workflow, WorkflowNode


TRIGGER_NODES = {"n8n-nodes-base.webhook", "n8n-nodes-base.formTrigger"}


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
