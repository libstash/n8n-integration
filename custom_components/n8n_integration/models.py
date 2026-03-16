"""Data models for n8n_integration."""

from __future__ import annotations

from typing import Any, TypedDict


class WorkflowNode(TypedDict, total=False):
    """TypedDict for workflow node."""

    id: str
    name: str
    type: str
    webhookId: str
    parameters: dict[str, Any]


class Workflow(TypedDict, total=False):
    """TypedDict for workflow."""

    id: str
    name: str
    updatedAt: str | None
    nodes: list[WorkflowNode]
