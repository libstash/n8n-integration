"""Todo platform for n8n_integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.todo import (
    TodoItem,
    TodoListEntity,
)
from homeassistant.components.todo.const import (
    TodoItemStatus,
    TodoListEntityFeature,
)

from .entity import N8nIntegrationEntity

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import N8nDataUpdateCoordinator
    from .data import N8nIntegrationConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 unused; Home Assistant passes it in
    entry: N8nIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the todo platform."""
    entity = N8nIntegrationTriggers(
        coordinator=entry.runtime_data.coordinator,
    )
    async_add_entities([entity])


class N8nIntegrationTriggers(N8nIntegrationEntity, TodoListEntity):
    """Simple read-only todo list with static example items."""

    _attr_name = "n8n triggers"
    _attr_has_entity_name = True
    _attr_supported_features = TodoListEntityFeature(0)

    def __init__(self, coordinator: N8nDataUpdateCoordinator) -> None:
        """Initialize the todo list entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._attr_unique_id}-triggers"
        # Get url and api_token from the integration's API client
        api_client = coordinator.config_entry.runtime_data.client
        url = getattr(api_client, "_url", None)

        workflows = coordinator.data["data"]

        # Generate todo items from workflows and their formTrigger nodes
        todo_items = []
        for workflow in workflows:
            workflow_id = workflow.get("id")
            workflow_name = workflow.get("name")
            # Add a todo item for each formTrigger node
            for node in workflow.get("nodes", []):
                if node.get("type") == "n8n-nodes-base.formTrigger":
                    node_id = node.get("id")
                    node_name = node.get("name")
                    form_url = f"{url}/form/{node.get('webhookId')}"
                    todo_items.append(
                        TodoItem(
                            uid=f"{workflow_id}-{node_id}",
                            summary=f"{workflow_name}: {node_name}",
                            description=form_url,
                            status=TodoItemStatus.NEEDS_ACTION,
                        )
                    )
                elif node.get("type") == "n8n-nodes-base.webhook":
                    node_id = node.get("id")
                    node_name = node.get("name")
                    todo_items.append(
                        TodoItem(
                            uid=f"{workflow_id}-{node_id}",
                            summary=f"{workflow_name}: {node_name}",
                            status=TodoItemStatus.NEEDS_ACTION,
                        )
                    )
        self._attr_todo_items = todo_items

    async def async_get_todo_items(self) -> list[TodoItem]:
        """Return the current todo items."""
        return list(self._attr_todo_items or [])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose todo items for template cards."""
        items = self._attr_todo_items or []
        return {
            "triggers": [
                {"id": item.uid, "name": item.summary, "description": item.description}
                for item in items
            ]
        }
