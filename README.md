# n8n Integration for Home Assistant

Connect Home Assistant to your n8n instance. This integration discovers active workflows, exposes webhook triggers as buttons you can use directly in Home Assistant or automate, and lists both webhook endpoints and form triggers.

## Requirements

- A reachable n8n base URL (for example, https://n8n.example.com).
- An n8n API token with permission to read workflows.
- tested with recent core build

## Installation

### Option 1: HACS (recommended)

1. In HACS, add this repository as a custom integration: `https://github.com/libstash/n8n-integration`.
2. Install **n8n Integration** from the Integrations section.
3. Restart Home Assistant.

### Option 2: Manual copy

1. Download this repository.
2. Copy the `custom_components/n8n_integration` folder into your Home Assistant `custom_components` directory.
3. Restart Home Assistant.

## Configuration

1. In Home Assistant, go to Settings → Devices & Services → Add Integration.
2. Search for **n8n Integration** and select it.
3. Enter your n8n base URL and API token. The flow validates the token by fetching active workflows.
4. After setup, entities are created automatically. If you rotate credentials later, use the integration's Options to update the URL/token.

## Entities

Entities are automatically grouped into Devices named after their parent n8n workflow.

### Buttons

One button is created for every Webhook node in each active workflow.

- **Action:** Pressing the button triggers the corresponding webhook in n8n.

### Sensors

Sensors represent active Webhook and Form triggers. These are read-only and include the following metadata in their state attributes:

- **Attributes:**
  - **workflow_id:** The unique ID of the n8n workflow.
  - **workflow_name:** The name of the workflow.
  - **n8n_url:** The base URL of your n8n instance.
  - **type:** The specific node type (e.g., n8n-nodes-base.formTrigger, n8n-nodes-base.webhook).
  - **form_url:** (Form triggers only) The direct URL to the n8n form.

## Example: Active n8n Form Triggers

This Markdown card dynamically lists available form triggers in the Home Assistant UI:

```jinja2
### Active n8n Form Triggers
{% set forms = states.sensor
  | selectattr('attributes.type', 'defined')
  | selectattr('attributes.type', 'eq', 'n8n-nodes-base.formTrigger')
  | list %}

{% if forms | length > 0 %}
| Workflow/Form Name | Workflow | Link |
| :--- | :---: | :---: |{% for state in forms %}
| {{ state.name }} | [✏️]({{ state.attributes.n8n_url }}/workflow/{{ state.attributes.workflow_id }}) | [🌐]({{ state.attributes.form_url }}) |{% endfor %}
{% else %}
> ℹ️ **No active form triggers found.** > Check if your n8n workflows are active and the integration is connected.
{% endif %}
```

# Example: Workflow Notifications (n8n to Home Assistant)

Set up Home Assistant notifications to monitor success or error results from your n8n workflows.

## 1. Data table

To track workflow outputs, create a table with the following schema:

```
id,workflowId,workflowName,message,type,createdAt,updatedAt
```

## 2. Error handler workflow

This workflow catches errors from other processes and logs an `error` entry into your Data Table.

![Error handler](<examples/Error handler workflow.png>)
[examples/Error handler.json](<examples/Error handler.json>)

## Workflow implementation

When building workflows that should report their status:

1. Open Workflow Settings.
2. Set the `Error Workflow (to notify when this one errors)` to point to your [Error handler workflow](#2-error-handler-workflow).

![Success or error workflow](<examples/Success or error workflow.png>)
![Form](<examples/Success or error form.png>)

[examples/Success or error.json](<examples/Success or error.json>)

## 4. Notifications Endpoint

This workflow acts as an API endpoint, allowing HomeAssistant to fetch the most recent workflow results.

![Notifications endpoint workflow](<examples/Notifications endpoint workflow.png>)
[examples/Notifications endpoint.json](<examples/Notifications endpoint.json>)

## Home Assistant Configuration

### Create Notifications

This automation processes the response from your n8n endpoint and generates a persistent notification for each entry.

**Setup:**

1. Go to the **n8n Integration**.
2. Select the **Notifications endpoint** entity.
3. Create a new automation using the following YAML:

```yaml
alias: Create notifications
description: ""
triggers:
  - trigger: state
    entity_id:
      - button.notifications_endpoint_webhook
    attribute: response
conditions: []
actions:
  - variables:
      messages: >-
        {{ state_attr('button.notifications_endpoint_webhook', 'response')
        }}
  - choose: []
    default:
      - repeat:
          for_each: "{{ messages }}"
          sequence:
            - data:
                message: "{{ repeat.item.message }}"
              action: notify.persistent_notification
mode: single
```

### Polling for Updates

Since the integration relies on a webhook response via a button press, use this automation to check for new notifications every minute:

```yaml
alias: Trigger Notifications Webhook Every Minute
description: Automatically press button.notifications_endpoint_webhook every minute
triggers:
  - minutes: "*"
    trigger: time_pattern
actions:
  - target:
      entity_id: button.notifications_endpoint_webhook
    action: button.press
mode: single
```

## How it works

- The integration pulls active workflows from n8n `GET /api/v1/workflows?active=true` using your API token.
- Only webhook and form triggers are displayed; other node types are ignored.
- **State Tracking:** A `_last_triggered_at` timestamp is added to webhooks query param to prevent duplicate notifications and filter for only the latest updates.

## Troubleshooting

- Auth errors: Confirm the API token is valid and belongs to the provided n8n URL.
- Connection errors: Ensure Home Assistant can reach the n8n URL (network, SSL, reverse proxy).
- Missing entities: Verify the workflows are active and contain `webhook` or `formTrigger` nodes.
