"""Button platform for n8n_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription

from .entity import N8nIntegrationEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import N8nDataUpdateCoordinator
    from .data import N8nIntegrationConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: N8nIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    workflows = entry.runtime_data.coordinator.data["data"]

    entities = []
    for workflow in workflows:
        workflow_id = str(workflow.get("id"))
        workflow_name = workflow.get("name", f"Workflow {workflow_id}")
        # Add a button for each webhook node in the workflow
        for node in workflow.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.webhook":
                node_id = str(node.get("id", node.get("name", "webhook")))
                node_name = node.get("name", f"Webhook {node_id}")
                entity_description = ButtonEntityDescription(
                    key=f"{workflow_id}-{node_id}",
                    name=f"{workflow_name}: {node_name}",
                    icon="mdi:gesture-tap",
                )
                entities.append(
                    N8nWorkflowButton(
                        coordinator=entry.runtime_data.coordinator,
                        entity_description=entity_description,
                        workflow_id=workflow_id,
                        webhook_node=node,
                    )
                )
    async_add_entities(entities)


class N8nWorkflowButton(N8nIntegrationEntity, ButtonEntity):
    """n8n_integration Button class."""

    def __init__(
        self,
        coordinator: N8nDataUpdateCoordinator,
        entity_description: ButtonEntityDescription,
        workflow_id: str,
        webhook_node: dict,
    ) -> None:
        """Initialize the button class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._webhook_node = webhook_node
        # Ensure unique_id is unique per workflow, node, and config entry
        node_id = str(webhook_node.get("id", webhook_node.get("name", "webhook")))
        self._attr_unique_id = f"{self._attr_unique_id}-{workflow_id}-{node_id}-button"
        self._last_triggered_at = None
        self._response = {}  # Local storage for API results

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {"response": self._response}

    async def async_press(self, **_: Any) -> None:
        """Handle the button press to trigger the workflow webhook node."""

        options = {}
        if self._last_triggered_at is not None:
            options["last_triggered_at"] = self._last_triggered_at

        result = await self.coordinator.config_entry.runtime_data.client.async_trigger_webhook(
            self._webhook_node, options
        )

        parameters = self._webhook_node.get("parameters", {})
        if parameters.get("responseMode") == "responseNode":
            self._response = result

        self._last_triggered_at = self.state
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
