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

## Example: Workflow Notifications (n8n to Home Assistant)

Push success or error messages from your n8n workflows to Home Assistant as persistent notifications.

### 1. Home Assistant: create the webhook automation

This automation listens on a Home Assistant webhook and creates a persistent notification for every message n8n sends.

1. Go to **Settings** → **Automations & Scenes** → **Create Automation**.
2. Open the menu (⋮) → **Edit in YAML** and paste:

```yaml
alias: Receive n8n notification
description: Create a persistent notification from an n8n webhook call
triggers:
  - trigger: webhook
    allowed_methods:
      - POST
      - PUT
    local_only: true
    webhook_id: n8n_notification
conditions: []
actions:
  - action: persistent_notification.create
    data:
      title: n8n
      message: >-
        {%- if trigger.json.type == 'error' -%}
          {{ trigger.json.workflowName }}: {{ trigger.json.message }}
        {%- else -%}
          {{ trigger.json.message }}
        {%- endif -%}
mode: queued
```

### 2. n8n: create the "Notify HomeAssistant" workflow

![Notify HomeAssistant](<examples/Notify HomeAssistant.png>)
[examples/Notify HomeAssistant.json](<examples/Notify HomeAssistant.json>)

Open the **HTTP Request** node and adjust the URL to your setup:

```
http://<your-home-assistant>:8123/api/webhook/<webhook_id>
```

The `webhook_id` must match the one in the automation above (`n8n_notification` by default).

### 3. n8n: send notifications from your workflows

In any workflow, add an **Execute Workflow** node that calls **Notify HomeAssistant** and passes an item with these fields:

1. Add an **Edit Fields (Set)** node and create these fields:

   | Field          | Description                                                                   |
   | :------------- | :---------------------------------------------------------------------------- |
   | `message`      | The notification text.                                                        |
   | `type`         | `success` or `error`                                                          |
   | `workflowName` | Name of the workflow that produced the message (e.g. `{{ $workflow.name }}`). |

2. Connect it to an **Execute Sub-workflow** and select **Notify HomeAssistant**.

The item that reaches Home Assistant then looks like this:

```json
{
  "type": "error",
  "workflowName": "Daily backup",
  "message": "Backup failed: disk full"
}
```

To get notified about failures automatically, create an error workflow with an **Error Trigger** node that calls **Notify HomeAssistant**, then select it under **Workflow Settings** → **Error Workflow** in the workflows you want to monitor.

## Troubleshooting

- Auth errors: Confirm the API token is valid and belongs to the provided n8n URL.
- Connection errors: Ensure Home Assistant can reach the n8n URL (network, SSL, reverse proxy).
- Missing entities: Verify the workflows are active and contain `webhook` or `formTrigger` nodes.
- Notifications not appearing: Check that the HTTP Request URL and `webhook_id` match the automation, and that n8n can reach Home Assistant. If n8n is outside your local network, disable `local_only`.
