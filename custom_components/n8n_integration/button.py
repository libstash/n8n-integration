"""Button platform for n8n_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.helpers.device_registry import DeviceInfo

from .entity import N8nIntegrationEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import N8nDataUpdateCoordinator
    from .data import N8nIntegrationConfigEntry
    from .models import Workflow, WorkflowNode


WEBHOOK_NODES = {"n8n-nodes-base.webhook"}


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: N8nIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    coordinator = entry.runtime_data.coordinator
    workflows: list[Workflow] = coordinator.data.get("data", [])

    entities: list[N8nWorkflowButton] = [
        N8nWorkflowButton(
            coordinator=coordinator,
            node=node,
            workflow=workflow,
        )
        for workflow in workflows
        for node in workflow.get("nodes", [])
        if node.get("type") in WEBHOOK_NODES
    ]

    async_add_entities(entities)


class N8nWorkflowButton(N8nIntegrationEntity, ButtonEntity):
    """n8n_integration Button class."""

    entity_description = ButtonEntityDescription(
        key="n8n_webhook_trigger",
    )

    def __init__(
        self,
        coordinator: N8nDataUpdateCoordinator,
        workflow: Workflow,
        node: WorkflowNode,
    ) -> None:
        """Initialize the button class."""
        super().__init__(coordinator)
        self._workflow = workflow
        self._node = node

        workflow_id = workflow.get("id")
        node_id = node.get("id")
        workflow_name = workflow.get("name")
        node_name = node.get("name")

        self._attr_unique_id = f"{self._attr_unique_id}-{workflow_id}-{node_id}-button"
        self._attr_icon = "mdi:gesture-tap"
        self._attr_name = f"{workflow_name}: {node_name}"

        self._last_triggered_at = None
        self._response = {}

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {"response": self._response}

    async def async_press(self, **_: Any) -> None:
        """Handle the button press to trigger the workflow webhook node."""
        options = {}
        if self._last_triggered_at is not None:
            options["_last_triggered_at"] = self._last_triggered_at

        client = self.coordinator.config_entry.runtime_data.client

        result = await client.async_trigger_webhook(self._node, options)

        parameters = self._node.get("parameters", {})
        if parameters.get("responseMode") == "responseNode":
            self._response = result

        self._last_triggered_at = self.state
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

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
