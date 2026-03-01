# n8n Integration for Home Assistant

Connect Home Assistant to your n8n instance. This integration discovers active workflows, exposes webhook triggers as buttons you can press from Home Assistant, and lists trigger endpoints and forms in the **n8n triggers** list.

## Features
- Creates a button entity for every `webhook` node in your active n8n workflows so you can fire the webhook from Home Assistant.
- Exposes a read-only triggers list entity that enumerates webhook and form triggers; form triggers include the generated form URL for convenience.
- Uses Home Assistant's config flow (UI setup) with validation against your n8n API.

## Requirements
- A reachable n8n base URL (for example, https://n8n.example.com).
- An n8n API token with permission to read workflows.
- tested with recent core build

## Installation
### Option 1: HACS (recommended)
1. In HACS, add this repository as a custom integration: `https://github.com/libstash/n8n-integration`.
2. Install **n8n Integration** from the Integrations section.

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
- Buttons: One per `webhook` node in each active workflow. Pressing the button triggers the corresponding webhook in n8n.
- Triggers list: A read-only list named **n8n triggers** containing webhook and form triggers. Items show workflow and node names; form trigger items include the form URL in the description.

## Example: trigger links card
Add a Markdown card that lists links to available form triggers:

```
{% set items = state_attr('todo.n8n_triggers', 'triggers') or [] %}

{% for item in items %}
- {% if item.description %}[{{ item.name }}]({{ item.description }}){% else %}{{ item.name }}{% endif %}
{% endfor %}
```

## How it works
- The integration pulls active workflows from `GET /api/v1/workflows?active=true` using your API token.
- Only webhook- and form-based triggers are surfaced; other node types are ignored.

## Troubleshooting
- Auth errors: Confirm the API token is valid and belongs to the provided n8n URL.
- Connection errors: Ensure Home Assistant can reach the n8n URL (network, SSL, reverse proxy).
- Missing entities: Verify the workflows are active and contain `webhook` or `formTrigger` nodes.
