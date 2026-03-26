"""FastMCP server with all Railway tool registrations."""

from typing import Annotated, Optional

from fastmcp import FastMCP
from pydantic import Field

from railway_mcp.client import get_client, RailwayAPIError
from railway_mcp.formatting import (
    _extract_edges,
    format_deployments_markdown,
    format_environments_markdown,
    format_logs_markdown,
    format_project_markdown,
    format_projects_markdown,
    format_response,
    format_service_instance_markdown,
    format_services_markdown,
    format_variables_markdown,
)
from railway_mcp.queries import (
    CREATE_ENVIRONMENT,
    DELETE_VARIABLE,
    GET_BUILD_LOGS,
    GET_DEPLOY_LOGS,
    GET_PROJECT,
    GET_SERVICE_INSTANCE,
    GET_VARIABLES,
    GET_VARIABLES_FOR_SERVICE_INSTANCE,
    LIST_DEPLOYMENTS,
    LIST_ENVIRONMENTS,
    LIST_PROJECTS,
    REDEPLOY_SERVICE,
    RESTART_DEPLOYMENT,
    UPSERT_VARIABLE,
    UPSERT_VARIABLE_COLLECTION,
)

mcp = FastMCP(
    "Railway MCP",
    instructions=(
        "Manage Railway infrastructure: projects, services, environments, "
        "variables, and deployments via the Railway GraphQL API."
    ),
)

# Type aliases for common annotated params
ProjectId = Annotated[str, Field(description="Railway project ID (UUID)")]
ServiceId = Annotated[str, Field(description="Railway service ID (UUID)")]
EnvironmentId = Annotated[str, Field(description="Railway environment ID (UUID)")]
DeploymentId = Annotated[str, Field(description="Deployment ID (get from railway_get_deployment_status)")]
ResponseFmt = Annotated[
    str,
    Field(
        default="markdown",
        description="Output format: 'markdown' for human-readable, 'json' for structured data",
    ),
]


# -- Projects -----------------------------------------------------------------


@mcp.tool(name="railway_list_projects")
async def list_projects(
    response_format: ResponseFmt = "markdown",
) -> str:
    """List all Railway projects accessible with your API token."""
    try:
        client = get_client()
        data = await client.execute(LIST_PROJECTS)
        projects = _extract_edges(data.get("projects", {}))
        if response_format == "json":
            return format_response(projects, "json")
        return format_projects_markdown(projects)
    except RailwayAPIError as e:
        return f"Error listing projects: {e}"


@mcp.tool(name="railway_get_project")
async def get_project(
    project_id: ProjectId,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Get details for a single Railway project by ID, including its services and environments."""
    try:
        client = get_client()
        data = await client.execute(GET_PROJECT, {"id": project_id})
        project = data.get("project")
        if not project:
            return f"Project `{project_id}` not found."
        if response_format == "json":
            return format_response(project, "json")
        return format_project_markdown(project)
    except RailwayAPIError as e:
        return f"Error fetching project: {e}"


# -- Services -----------------------------------------------------------------


@mcp.tool(name="railway_list_services")
async def list_services(
    project_id: ProjectId,
    response_format: ResponseFmt = "markdown",
) -> str:
    """List all services in a Railway project."""
    try:
        client = get_client()
        data = await client.execute(GET_PROJECT, {"id": project_id})
        project = data.get("project")
        if not project:
            return f"Project `{project_id}` not found."
        services = _extract_edges(project.get("services", {}))
        if response_format == "json":
            return format_response(services, "json")
        return format_services_markdown(services)
    except RailwayAPIError as e:
        return f"Error listing services: {e}"


@mcp.tool(name="railway_get_service")
async def get_service(
    service_id: ServiceId,
    environment_id: EnvironmentId,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Get service configuration for a specific environment, including build/start commands, region, and latest deployment."""
    try:
        client = get_client()
        data = await client.execute(
            GET_SERVICE_INSTANCE,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        instance = data.get("serviceInstance")
        if not instance:
            return "Service instance not found for that service/environment combination."
        if response_format == "json":
            return format_response(instance, "json")
        return format_service_instance_markdown(instance)
    except RailwayAPIError as e:
        return f"Error fetching service: {e}"


# -- Environments -------------------------------------------------------------


@mcp.tool(name="railway_list_environments")
async def list_environments(
    project_id: ProjectId,
    response_format: ResponseFmt = "markdown",
) -> str:
    """List all environments in a Railway project."""
    try:
        client = get_client()
        data = await client.execute(
            LIST_ENVIRONMENTS, {"projectId": project_id}
        )
        project = data.get("project")
        if not project:
            return f"Project `{project_id}` not found."
        envs = _extract_edges(project.get("environments", {}))
        if response_format == "json":
            return format_response(envs, "json")
        return format_environments_markdown(envs)
    except RailwayAPIError as e:
        return f"Error listing environments: {e}"


@mcp.tool(name="railway_create_environment")
async def create_environment(
    project_id: ProjectId,
    name: Annotated[str, Field(description="Name for the new environment (e.g. 'staging', 'dev')")],
    ephemeral: Annotated[bool, Field(description="If true, creates a temporary PR-style environment")] = False,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Create a new environment in a Railway project. Use ephemeral=true for temporary PR-style environments."""
    try:
        client = get_client()
        gql_vars = {
            "input": {
                "projectId": project_id,
                "name": name,
                "ephemeral": ephemeral,
            }
        }
        data = await client.execute(CREATE_ENVIRONMENT, gql_vars)
        env = data.get("environmentCreate")
        if not env:
            return "Failed to create environment. No data returned."
        if response_format == "json":
            return format_response(env, "json")
        return (
            f"Environment **{env['name']}** created successfully.\n"
            f"ID: `{env['id']}`"
        )
    except RailwayAPIError as e:
        return f"Error creating environment: {e}"


@mcp.tool(name="railway_duplicate_environment")
async def duplicate_environment(
    project_id: ProjectId,
    source_environment_id: Annotated[str, Field(description="ID of the environment to duplicate")],
    name: Annotated[str, Field(description="Name for the duplicated environment")],
    response_format: ResponseFmt = "markdown",
) -> str:
    """Duplicate an existing environment, copying all its variables and service configs."""
    try:
        client = get_client()
        gql_vars = {
            "input": {
                "projectId": project_id,
                "sourceEnvironmentId": source_environment_id,
                "name": name,
            }
        }
        data = await client.execute(CREATE_ENVIRONMENT, gql_vars)
        env = data.get("environmentCreate")
        if not env:
            return "Failed to duplicate environment. No data returned."
        if response_format == "json":
            return format_response(env, "json")
        return (
            f"Environment **{env['name']}** duplicated successfully.\n"
            f"ID: `{env['id']}`"
        )
    except RailwayAPIError as e:
        return f"Error duplicating environment: {e}"


# -- Variables ----------------------------------------------------------------


@mcp.tool(name="railway_list_variables")
async def list_variables(
    project_id: ProjectId,
    environment_id: EnvironmentId,
    service_id: Annotated[Optional[str], Field(description="Service ID. If omitted, returns shared/environment-level variables.")] = None,
    response_format: ResponseFmt = "markdown",
) -> str:
    """List all resolved variables for a service or shared environment. Values are fully interpolated."""
    try:
        client = get_client()
        gql_vars: dict = {
            "projectId": project_id,
            "environmentId": environment_id,
        }
        if service_id:
            gql_vars["serviceId"] = service_id
        data = await client.execute(GET_VARIABLES, gql_vars)
        vars_dict = data.get("variables", {})
        if response_format == "json":
            return format_response(vars_dict, "json")
        return format_variables_markdown(vars_dict)
    except RailwayAPIError as e:
        return f"Error listing variables: {e}"


@mcp.tool(name="railway_get_variables_unresolved")
async def get_variables_unresolved(
    project_id: ProjectId,
    environment_id: EnvironmentId,
    service_id: Annotated[Optional[str], Field(description="Service ID. If omitted, returns shared variables.")] = None,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Get variables with template references intact (e.g. ${{shared.DATABASE_URL}}). Useful for understanding variable dependencies."""
    try:
        client = get_client()
        gql_vars: dict = {
            "projectId": project_id,
            "environmentId": environment_id,
        }
        if service_id:
            gql_vars["serviceId"] = service_id
        data = await client.execute(
            GET_VARIABLES_FOR_SERVICE_INSTANCE, gql_vars
        )
        vars_dict = data.get("variablesForServiceInstance", {})
        if response_format == "json":
            return format_response(vars_dict, "json")
        return format_variables_markdown(vars_dict)
    except RailwayAPIError as e:
        return f"Error fetching unresolved variables: {e}"


@mcp.tool(name="railway_set_variable")
async def set_variable(
    project_id: ProjectId,
    environment_id: EnvironmentId,
    name: Annotated[str, Field(description="Variable name (e.g. 'DATABASE_URL', 'SECRET_KEY')")],
    value: Annotated[str, Field(description="Variable value")],
    service_id: Annotated[Optional[str], Field(description="Service ID. If omitted, sets a shared/environment variable.")] = None,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Set (create or update) a single environment variable on a service or shared environment."""
    try:
        client = get_client()
        gql_vars: dict = {
            "input": {
                "projectId": project_id,
                "environmentId": environment_id,
                "name": name,
                "value": value,
            }
        }
        if service_id:
            gql_vars["input"]["serviceId"] = service_id
        await client.execute(UPSERT_VARIABLE, gql_vars)
        return f"Variable `{name}` set successfully."
    except RailwayAPIError as e:
        return f"Error setting variable: {e}"


@mcp.tool(
    name="railway_bulk_set_variables",
    annotations={"destructiveHint": True},
)
async def bulk_set_variables(
    project_id: ProjectId,
    environment_id: EnvironmentId,
    variables: Annotated[dict[str, str], Field(description="Key-value dict of variables to set (e.g. {'KEY': 'value', 'OTHER': 'val2'})")],
    service_id: Annotated[Optional[str], Field(description="Service ID. If omitted, sets shared/environment variables.")] = None,
    replace: Annotated[bool, Field(description="WARNING: If true, all existing variables NOT in this dict will be DELETED. Default false (merge/upsert only).")] = False,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Set multiple variables at once. WARNING: if replace=true, variables not in the dict will be DELETED."""
    try:
        client = get_client()
        gql_vars: dict = {
            "input": {
                "projectId": project_id,
                "environmentId": environment_id,
                "variables": variables,
                "replace": replace,
            }
        }
        if service_id:
            gql_vars["input"]["serviceId"] = service_id
        await client.execute(UPSERT_VARIABLE_COLLECTION, gql_vars)
        count = len(variables)
        mode = "replaced" if replace else "upserted"
        return f"Successfully {mode} {count} variable(s)."
    except RailwayAPIError as e:
        return f"Error bulk setting variables: {e}"


@mcp.tool(
    name="railway_delete_variable",
    annotations={"destructiveHint": True},
)
async def delete_variable(
    project_id: ProjectId,
    environment_id: EnvironmentId,
    name: Annotated[str, Field(description="Name of the variable to delete")],
    service_id: Annotated[Optional[str], Field(description="Service ID. If omitted, deletes a shared variable.")] = None,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Delete a single environment variable. This action cannot be undone."""
    try:
        client = get_client()
        gql_vars: dict = {
            "input": {
                "projectId": project_id,
                "environmentId": environment_id,
                "name": name,
            }
        }
        if service_id:
            gql_vars["input"]["serviceId"] = service_id
        await client.execute(DELETE_VARIABLE, gql_vars)
        return f"Variable `{name}` deleted successfully."
    except RailwayAPIError as e:
        return f"Error deleting variable: {e}"


# -- Deployments --------------------------------------------------------------


@mcp.tool(name="railway_get_deployment_status")
async def get_deployment_status(
    project_id: ProjectId,
    environment_id: EnvironmentId,
    service_id: ServiceId,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Get the latest deployment(s) for a service in an environment, including status and URLs."""
    try:
        client = get_client()
        gql_vars = {
            "projectId": project_id,
            "environmentId": environment_id,
            "serviceId": service_id,
            "first": 5,
        }
        data = await client.execute(LIST_DEPLOYMENTS, gql_vars)
        deployments = _extract_edges(data.get("deployments", {}))
        if response_format == "json":
            return format_response(deployments, "json")
        return format_deployments_markdown(deployments)
    except RailwayAPIError as e:
        return f"Error fetching deployment status: {e}"


@mcp.tool(name="railway_get_build_logs")
async def get_build_logs(
    deployment_id: DeploymentId,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Fetch build logs for a specific deployment. Get the deployment ID from railway_get_deployment_status."""
    try:
        client = get_client()
        data = await client.execute(
            GET_BUILD_LOGS, {"deploymentId": deployment_id}
        )
        logs = data.get("buildLogs", [])
        if response_format == "json":
            return format_response(logs, "json")
        return format_logs_markdown(logs, "Build Logs")
    except RailwayAPIError as e:
        return f"Error fetching build logs: {e}"


@mcp.tool(name="railway_get_deploy_logs")
async def get_deploy_logs(
    deployment_id: DeploymentId,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Fetch runtime/deploy logs for a specific deployment. Get the deployment ID from railway_get_deployment_status."""
    try:
        client = get_client()
        data = await client.execute(
            GET_DEPLOY_LOGS, {"deploymentId": deployment_id}
        )
        logs = data.get("deploymentLogs", [])
        if response_format == "json":
            return format_response(logs, "json")
        return format_logs_markdown(logs, "Deploy Logs")
    except RailwayAPIError as e:
        return f"Error fetching deploy logs: {e}"


@mcp.tool(name="railway_redeploy")
async def redeploy(
    service_id: ServiceId,
    environment_id: EnvironmentId,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Trigger a full redeploy (rebuild + deploy) for a service in an environment."""
    try:
        client = get_client()
        await client.execute(
            REDEPLOY_SERVICE,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        return "Redeploy triggered successfully. Use railway_get_deployment_status to monitor progress."
    except RailwayAPIError as e:
        return f"Error triggering redeploy: {e}"


@mcp.tool(name="railway_restart_deployment")
async def restart_deployment(
    deployment_id: DeploymentId,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Restart a deployment without rebuilding. Useful for picking up new environment variables."""
    try:
        client = get_client()
        await client.execute(
            RESTART_DEPLOYMENT, {"id": deployment_id}
        )
        return "Deployment restarted successfully."
    except RailwayAPIError as e:
        return f"Error restarting deployment: {e}"
