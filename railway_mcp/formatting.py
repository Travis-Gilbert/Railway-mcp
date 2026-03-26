"""Response formatting helpers for markdown and JSON output."""

import json
from datetime import datetime


def format_response(data: dict | list | str, fmt: str = "markdown") -> str:
    """Route to the appropriate formatter."""
    if fmt == "json":
        return json.dumps(data, indent=2, default=str)
    return str(data)


def format_timestamp(ts: str | None) -> str:
    """Convert an ISO timestamp to a human-readable string."""
    if not ts:
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, AttributeError):
        return ts


# -- Project formatters -------------------------------------------------------


def format_projects_markdown(projects: list[dict]) -> str:
    """Format a list of projects as markdown."""
    if not projects:
        return "No projects found."
    lines = ["# Railway Projects", ""]
    for p in projects:
        lines.append(f"## {p.get('name', 'Unnamed')}")
        lines.append(f"**ID:** `{p['id']}`")
        if p.get("description"):
            lines.append(f"**Description:** {p['description']}")
        lines.append(f"**Created:** {format_timestamp(p.get('createdAt'))}")

        envs = _extract_edges(p.get("environments", {}))
        if envs:
            lines.append("**Environments:**")
            for e in envs:
                lines.append(f"  - {e['name']} (`{e['id']}`)")

        services = _extract_edges(p.get("services", {}))
        if services:
            lines.append("**Services:**")
            for s in services:
                icon = f" {s['icon']}" if s.get("icon") else ""
                lines.append(f"  - {s['name']}{icon} (`{s['id']}`)")

        lines.append("")
    return "\n".join(lines)


def format_project_markdown(project: dict) -> str:
    """Format a single project as markdown."""
    return format_projects_markdown([project])


# -- Service formatters -------------------------------------------------------


def format_services_markdown(services: list[dict]) -> str:
    """Format a list of services as markdown."""
    if not services:
        return "No services found in this project."
    lines = ["# Services", ""]
    for s in services:
        icon = f" {s['icon']}" if s.get("icon") else ""
        lines.append(f"- **{s['name']}**{icon}  ID: `{s['id']}`")
    return "\n".join(lines)


def format_service_instance_markdown(instance: dict) -> str:
    """Format a service instance (service + environment config)."""
    lines = [
        f"# Service: {instance.get('serviceName', 'Unknown')}",
        "",
        f"**Start command:** `{instance.get('startCommand') or 'default'}`",
        f"**Build command:** `{instance.get('buildCommand') or 'default'}`",
        f"**Root directory:** `{instance.get('rootDirectory') or '/'}`",
        f"**Region:** {instance.get('region') or 'auto'}",
        f"**Replicas:** {instance.get('numReplicas', 1)}",
        f"**Restart policy:** {instance.get('restartPolicyType', 'N/A')}",
    ]
    if instance.get("healthcheckPath"):
        lines.append(f"**Healthcheck:** `{instance['healthcheckPath']}`")
    dep = instance.get("latestDeployment")
    if dep:
        lines.append("")
        lines.append("**Latest deployment:**")
        lines.append(f"  - Status: {dep.get('status', 'unknown')}")
        lines.append(f"  - ID: `{dep['id']}`")
        lines.append(
            f"  - Created: {format_timestamp(dep.get('createdAt'))}"
        )
    return "\n".join(lines)


# -- Environment formatters ---------------------------------------------------


def format_environments_markdown(environments: list[dict]) -> str:
    """Format a list of environments."""
    if not environments:
        return "No environments found."
    lines = ["# Environments", ""]
    for e in environments:
        lines.append(f"- **{e['name']}**  ID: `{e['id']}`")
    return "\n".join(lines)


# -- Variable formatters ------------------------------------------------------


def format_variables_markdown(variables: dict) -> str:
    """Format variables as a markdown table."""
    if not variables:
        return "No variables found."
    lines = ["# Variables", "", "| Name | Value |", "|------|-------|"]
    for key in sorted(variables.keys()):
        val = variables[key]
        # Truncate long values for readability
        display = val if len(val) <= 80 else val[:77] + "..."
        # Escape pipes in values
        display = display.replace("|", "\\|")
        lines.append(f"| `{key}` | `{display}` |")
    return "\n".join(lines)


# -- Deployment formatters ----------------------------------------------------


def format_deployments_markdown(deployments: list[dict]) -> str:
    """Format deployment list."""
    if not deployments:
        return "No deployments found."
    lines = ["# Deployments", ""]
    for d in deployments:
        status = d.get("status", "unknown")
        lines.append(f"- **{status}** `{d['id']}`")
        lines.append(
            f"  Created: {format_timestamp(d.get('createdAt'))}"
        )
        if d.get("staticUrl"):
            lines.append(f"  URL: {d['staticUrl']}")
        if d.get("canRollback"):
            lines.append("  (rollback available)")
        lines.append("")
    return "\n".join(lines)


def format_logs_markdown(logs: list[dict], title: str = "Logs") -> str:
    """Format log entries as markdown."""
    if not logs:
        return f"No {title.lower()} found."
    lines = [f"# {title}", ""]
    for entry in logs:
        ts = format_timestamp(entry.get("timestamp"))
        severity = entry.get("severity", "")
        msg = entry.get("message", "")
        prefix = f"[{severity}]" if severity else ""
        lines.append(f"`{ts}` {prefix} {msg}")
    return "\n".join(lines)


# -- Helpers ------------------------------------------------------------------


def _extract_edges(relay_connection: dict) -> list[dict]:
    """Extract nodes from a Relay-style edges/node structure."""
    edges = relay_connection.get("edges", [])
    return [edge["node"] for edge in edges if "node" in edge]
