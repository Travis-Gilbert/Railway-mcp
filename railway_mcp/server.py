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
    DEPLOY_SERVICE,
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
    SERVICE_CONNECT,
    SERVICE_CREATE,
    SERVICE_DELETE,
    SERVICE_DISCONNECT,
    SERVICE_INSTANCE_UPDATE,
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


@mcp.tool(name="railway_create_service")
async def create_service(
    project_id: ProjectId,
    name: Annotated[Optional[str], Field(description="Service name (optional, Railway auto-generates if omitted)")] = None,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Create a new empty service in a project.

    After creating, use railway_connect_service to attach a GitHub repo
    (which triggers the first deploy), or railway_update_service to
    configure the Dockerfile path, start command, etc.
    """
    try:
        client = get_client()
        input_data: dict = {"projectId": project_id}
        if name:
            input_data["name"] = name
        data = await client.execute(SERVICE_CREATE, {"input": input_data})
        svc = data.get("serviceCreate")
        if not svc:
            return "Failed to create service. No data returned."
        if response_format == "json":
            return format_response(svc, "json")
        return (
            f"Service **{svc.get('name', 'unnamed')}** created successfully.\n"
            f"ID: `{svc['id']}`\n\n"
            f"Next steps:\n"
            f"1. Use `railway_connect_service` to attach a GitHub repo\n"
            f"2. Use `railway_update_service` to set Dockerfile path, start command, etc."
        )
    except RailwayAPIError as e:
        return f"Error creating service: {e}"


@mcp.tool(
    name="railway_delete_service",
    annotations={"destructiveHint": True},
)
async def delete_service(
    service_id: ServiceId,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Permanently delete a service. This cannot be undone. All deployments and data will be lost."""
    try:
        client = get_client()
        await client.execute(SERVICE_DELETE, {"id": service_id})
        return f"Service `{service_id}` deleted successfully."
    except RailwayAPIError as e:
        return f"Error deleting service: {e}"


@mcp.tool(name="railway_connect_service")
async def connect_service(
    service_id: ServiceId,
    repo: Annotated[str, Field(description="GitHub repo in 'owner/repo' format (e.g. 'Travis-Gilbert/index-api')")],
    branch: Annotated[str, Field(description="Branch to deploy from (e.g. 'main')")] = "main",
    response_format: ResponseFmt = "markdown",
) -> str:
    """Connect a GitHub repository to a service. This triggers a deploy from the repo.

    Use this after railway_create_service to attach a source.
    The service will build and deploy from the specified repo and branch.
    """
    try:
        client = get_client()
        data = await client.execute(
            SERVICE_CONNECT,
            {"id": service_id, "input": {"repo": repo, "branch": branch}},
        )
        svc = data.get("serviceConnect")
        if not svc:
            return "Failed to connect service. No data returned."
        if response_format == "json":
            return format_response(svc, "json")
        return (
            f"Service connected to **{repo}** (branch: {branch}).\n"
            f"A deploy has been triggered automatically."
        )
    except RailwayAPIError as e:
        return f"Error connecting service: {e}"


@mcp.tool(name="railway_disconnect_service")
async def disconnect_service(
    service_id: ServiceId,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Disconnect a service from its source repo or image. The service will remain but won't receive new deploys."""
    try:
        client = get_client()
        await client.execute(SERVICE_DISCONNECT, {"id": service_id})
        return f"Service `{service_id}` disconnected from its source."
    except RailwayAPIError as e:
        return f"Error disconnecting service: {e}"


@mcp.tool(name="railway_update_service")
async def update_service(
    service_id: ServiceId,
    environment_id: EnvironmentId,
    dockerfile_path: Annotated[Optional[str], Field(description="Path to Dockerfile (e.g. 'Dockerfile.mcp'). Overrides railway.toml.")] = None,
    start_command: Annotated[Optional[str], Field(description="Custom start command (e.g. 'python -m mcp_server.server')")] = None,
    build_command: Annotated[Optional[str], Field(description="Custom build command")] = None,
    root_directory: Annotated[Optional[str], Field(description="Root directory for the build context (e.g. 'backend/')")] = None,
    healthcheck_path: Annotated[Optional[str], Field(description="HTTP path for health checks (e.g. '/health')")] = None,
    num_replicas: Annotated[Optional[int], Field(description="Number of replicas (1 for single instance)")] = None,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Update service instance configuration: Dockerfile path, start command, build command, root directory, health check path, and replica count.

    This writes configuration but does NOT trigger a deploy.
    After updating, use railway_deploy to apply the changes.

    This is the tool that overrides railway.toml settings per-service.
    For example, to fix a service deploying with the wrong Dockerfile,
    set dockerfile_path='Dockerfile.mcp' here.
    """
    try:
        input_data: dict = {}
        if dockerfile_path is not None:
            input_data["dockerfilePath"] = dockerfile_path
        if start_command is not None:
            input_data["startCommand"] = start_command
        if build_command is not None:
            input_data["buildCommand"] = build_command
        if root_directory is not None:
            input_data["rootDirectory"] = root_directory
        if healthcheck_path is not None:
            input_data["healthcheckPath"] = healthcheck_path
        if num_replicas is not None:
            input_data["numReplicas"] = num_replicas

        if not input_data:
            return "No fields to update. Provide at least one of: dockerfile_path, start_command, build_command, root_directory, healthcheck_path, num_replicas."

        client = get_client()
        await client.execute(
            SERVICE_INSTANCE_UPDATE,
            {
                "serviceId": service_id,
                "environmentId": environment_id,
                "input": input_data,
            },
        )

        updated = ", ".join(f"{k}={v}" for k, v in input_data.items())
        return (
            f"Service config updated: {updated}\n\n"
            f"**Important:** This writes configuration only. "
            f"Use `railway_deploy` to apply the changes."
        )
    except RailwayAPIError as e:
        return f"Error updating service: {e}"


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
    """Trigger a full redeploy (rebuild + deploy) for a service in an environment. Uses the existing source and config."""
    try:
        client = get_client()
        await client.execute(
            REDEPLOY_SERVICE,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        return "Redeploy triggered successfully. Use railway_get_deployment_status to monitor progress."
    except RailwayAPIError as e:
        return f"Error triggering redeploy: {e}"


@mcp.tool(name="railway_deploy")
async def deploy(
    service_id: ServiceId,
    environment_id: EnvironmentId,
    response_format: ResponseFmt = "markdown",
) -> str:
    """Trigger a fresh deploy for a service. Use this after railway_update_service to apply config changes.

    Unlike railway_redeploy, this creates a new deployment that picks up
    any staged config changes (Dockerfile path, start command, etc.).
    """
    try:
        client = get_client()
        await client.execute(
            DEPLOY_SERVICE,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        return "Deploy triggered successfully. Use railway_get_deployment_status to monitor progress."
    except RailwayAPIError as e:
        return f"Error triggering deploy: {e}"


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
