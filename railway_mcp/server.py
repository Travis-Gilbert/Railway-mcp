"""FastMCP server with all Railway tool registrations."""

from fastmcp import FastMCP

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
from railway_mcp.models import (
    BulkSetVariablesInput,
    CreateEnvironmentInput,
    DeleteVariableInput,
    DuplicateEnvironmentInput,
    GetBuildLogsInput,
    GetDeployLogsInput,
    GetDeploymentStatusInput,
    GetProjectInput,
    GetServiceInput,
    GetVariablesUnresolvedInput,
    ListEnvironmentsInput,
    ListProjectsInput,
    ListServicesInput,
    ListVariablesInput,
    RedeployInput,
    RestartDeploymentInput,
    SetVariableInput,
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


# -- Projects -----------------------------------------------------------------


@mcp.tool(name="railway_list_projects")
async def list_projects(input: ListProjectsInput) -> str:
    """List all Railway projects accessible with your API token."""
    try:
        client = get_client()
        data = await client.execute(LIST_PROJECTS)
        projects = _extract_edges(data.get("projects", {}))
        if input.response_format.value == "json":
            return format_response(projects, "json")
        return format_projects_markdown(projects)
    except RailwayAPIError as e:
        return f"Error listing projects: {e}"


@mcp.tool(name="railway_get_project")
async def get_project(input: GetProjectInput) -> str:
    """Get details for a single Railway project by ID, including its services and environments."""
    try:
        client = get_client()
        data = await client.execute(GET_PROJECT, {"id": input.project_id})
        project = data.get("project")
        if not project:
            return f"Project `{input.project_id}` not found."
        if input.response_format.value == "json":
            return format_response(project, "json")
        return format_project_markdown(project)
    except RailwayAPIError as e:
        return f"Error fetching project: {e}"


# -- Services -----------------------------------------------------------------


@mcp.tool(name="railway_list_services")
async def list_services(input: ListServicesInput) -> str:
    """List all services in a Railway project."""
    try:
        client = get_client()
        data = await client.execute(GET_PROJECT, {"id": input.project_id})
        project = data.get("project")
        if not project:
            return f"Project `{input.project_id}` not found."
        services = _extract_edges(project.get("services", {}))
        if input.response_format.value == "json":
            return format_response(services, "json")
        return format_services_markdown(services)
    except RailwayAPIError as e:
        return f"Error listing services: {e}"


@mcp.tool(name="railway_get_service")
async def get_service(input: GetServiceInput) -> str:
    """Get service configuration for a specific environment, including build/start commands, region, and latest deployment."""
    try:
        client = get_client()
        data = await client.execute(
            GET_SERVICE_INSTANCE,
            {
                "serviceId": input.service_id,
                "environmentId": input.environment_id,
            },
        )
        instance = data.get("serviceInstance")
        if not instance:
            return "Service instance not found for that service/environment combination."
        if input.response_format.value == "json":
            return format_response(instance, "json")
        return format_service_instance_markdown(instance)
    except RailwayAPIError as e:
        return f"Error fetching service: {e}"


# -- Environments -------------------------------------------------------------


@mcp.tool(name="railway_list_environments")
async def list_environments(input: ListEnvironmentsInput) -> str:
    """List all environments in a Railway project."""
    try:
        client = get_client()
        data = await client.execute(
            LIST_ENVIRONMENTS, {"projectId": input.project_id}
        )
        project = data.get("project")
        if not project:
            return f"Project `{input.project_id}` not found."
        envs = _extract_edges(project.get("environments", {}))
        if input.response_format.value == "json":
            return format_response(envs, "json")
        return format_environments_markdown(envs)
    except RailwayAPIError as e:
        return f"Error listing environments: {e}"


@mcp.tool(name="railway_create_environment")
async def create_environment(input: CreateEnvironmentInput) -> str:
    """Create a new environment in a Railway project. Use ephemeral=true for temporary PR-style environments."""
    try:
        client = get_client()
        variables = {
            "input": {
                "projectId": input.project_id,
                "name": input.name,
                "ephemeral": input.ephemeral,
            }
        }
        data = await client.execute(CREATE_ENVIRONMENT, variables)
        env = data.get("environmentCreate")
        if not env:
            return "Failed to create environment. No data returned."
        if input.response_format.value == "json":
            return format_response(env, "json")
        return (
            f"Environment **{env['name']}** created successfully.\n"
            f"ID: `{env['id']}`"
        )
    except RailwayAPIError as e:
        return f"Error creating environment: {e}"


@mcp.tool(name="railway_duplicate_environment")
async def duplicate_environment(input: DuplicateEnvironmentInput) -> str:
    """Duplicate an existing environment, copying all its variables and service configs."""
    try:
        client = get_client()
        variables = {
            "input": {
                "projectId": input.project_id,
                "sourceEnvironmentId": input.source_environment_id,
                "name": input.name,
            }
        }
        data = await client.execute(CREATE_ENVIRONMENT, variables)
        env = data.get("environmentCreate")
        if not env:
            return "Failed to duplicate environment. No data returned."
        if input.response_format.value == "json":
            return format_response(env, "json")
        return (
            f"Environment **{env['name']}** duplicated successfully.\n"
            f"ID: `{env['id']}`"
        )
    except RailwayAPIError as e:
        return f"Error duplicating environment: {e}"


# -- Variables ----------------------------------------------------------------


@mcp.tool(name="railway_list_variables")
async def list_variables(input: ListVariablesInput) -> str:
    """List all resolved variables for a service or shared environment. Values are fully interpolated."""
    try:
        client = get_client()
        variables = {
            "projectId": input.project_id,
            "environmentId": input.environment_id,
        }
        if input.service_id:
            variables["serviceId"] = input.service_id
        data = await client.execute(GET_VARIABLES, variables)
        vars_dict = data.get("variables", {})
        if input.response_format.value == "json":
            return format_response(vars_dict, "json")
        return format_variables_markdown(vars_dict)
    except RailwayAPIError as e:
        return f"Error listing variables: {e}"


@mcp.tool(name="railway_get_variables_unresolved")
async def get_variables_unresolved(input: GetVariablesUnresolvedInput) -> str:
    """Get variables with template references intact (e.g. ${{shared.DATABASE_URL}}). Useful for understanding variable dependencies."""
    try:
        client = get_client()
        variables = {
            "projectId": input.project_id,
            "environmentId": input.environment_id,
        }
        if input.service_id:
            variables["serviceId"] = input.service_id
        data = await client.execute(
            GET_VARIABLES_FOR_SERVICE_INSTANCE, variables
        )
        vars_dict = data.get("variablesForServiceInstance", {})
        if input.response_format.value == "json":
            return format_response(vars_dict, "json")
        return format_variables_markdown(vars_dict)
    except RailwayAPIError as e:
        return f"Error fetching unresolved variables: {e}"


@mcp.tool(name="railway_set_variable")
async def set_variable(input: SetVariableInput) -> str:
    """Set (create or update) a single environment variable on a service or shared environment."""
    try:
        client = get_client()
        variables = {
            "input": {
                "projectId": input.project_id,
                "environmentId": input.environment_id,
                "name": input.name,
                "value": input.value,
            }
        }
        if input.service_id:
            variables["input"]["serviceId"] = input.service_id
        await client.execute(UPSERT_VARIABLE, variables)
        return f"Variable `{input.name}` set successfully."
    except RailwayAPIError as e:
        return f"Error setting variable: {e}"


@mcp.tool(
    name="railway_bulk_set_variables",
    annotations={"destructiveHint": True},
)
async def bulk_set_variables(input: BulkSetVariablesInput) -> str:
    """Set multiple variables at once. WARNING: if replace=true, variables not in the dict will be DELETED."""
    try:
        client = get_client()
        variables = {
            "input": {
                "projectId": input.project_id,
                "environmentId": input.environment_id,
                "variables": input.variables,
                "replace": input.replace,
            }
        }
        if input.service_id:
            variables["input"]["serviceId"] = input.service_id
        await client.execute(UPSERT_VARIABLE_COLLECTION, variables)
        count = len(input.variables)
        mode = "replaced" if input.replace else "upserted"
        return f"Successfully {mode} {count} variable(s)."
    except RailwayAPIError as e:
        return f"Error bulk setting variables: {e}"


@mcp.tool(
    name="railway_delete_variable",
    annotations={"destructiveHint": True},
)
async def delete_variable(input: DeleteVariableInput) -> str:
    """Delete a single environment variable. This action cannot be undone."""
    try:
        client = get_client()
        variables = {
            "input": {
                "projectId": input.project_id,
                "environmentId": input.environment_id,
                "name": input.name,
            }
        }
        if input.service_id:
            variables["input"]["serviceId"] = input.service_id
        await client.execute(DELETE_VARIABLE, variables)
        return f"Variable `{input.name}` deleted successfully."
    except RailwayAPIError as e:
        return f"Error deleting variable: {e}"


# -- Deployments --------------------------------------------------------------


@mcp.tool(name="railway_get_deployment_status")
async def get_deployment_status(input: GetDeploymentStatusInput) -> str:
    """Get the latest deployment(s) for a service in an environment, including status and URLs."""
    try:
        client = get_client()
        variables = {
            "projectId": input.project_id,
            "environmentId": input.environment_id,
            "serviceId": input.service_id,
            "first": 5,
        }
        data = await client.execute(LIST_DEPLOYMENTS, variables)
        deployments = _extract_edges(data.get("deployments", {}))
        if input.response_format.value == "json":
            return format_response(deployments, "json")
        return format_deployments_markdown(deployments)
    except RailwayAPIError as e:
        return f"Error fetching deployment status: {e}"


@mcp.tool(name="railway_get_build_logs")
async def get_build_logs(input: GetBuildLogsInput) -> str:
    """Fetch build logs for a specific deployment. Get the deployment ID from railway_get_deployment_status."""
    try:
        client = get_client()
        data = await client.execute(
            GET_BUILD_LOGS, {"deploymentId": input.deployment_id}
        )
        logs = data.get("buildLogs", [])
        if input.response_format.value == "json":
            return format_response(logs, "json")
        return format_logs_markdown(logs, "Build Logs")
    except RailwayAPIError as e:
        return f"Error fetching build logs: {e}"


@mcp.tool(name="railway_get_deploy_logs")
async def get_deploy_logs(input: GetDeployLogsInput) -> str:
    """Fetch runtime/deploy logs for a specific deployment. Get the deployment ID from railway_get_deployment_status."""
    try:
        client = get_client()
        data = await client.execute(
            GET_DEPLOY_LOGS, {"deploymentId": input.deployment_id}
        )
        logs = data.get("deploymentLogs", [])
        if input.response_format.value == "json":
            return format_response(logs, "json")
        return format_logs_markdown(logs, "Deploy Logs")
    except RailwayAPIError as e:
        return f"Error fetching deploy logs: {e}"


@mcp.tool(name="railway_redeploy")
async def redeploy(input: RedeployInput) -> str:
    """Trigger a full redeploy (rebuild + deploy) for a service in an environment."""
    try:
        client = get_client()
        await client.execute(
            REDEPLOY_SERVICE,
            {
                "serviceId": input.service_id,
                "environmentId": input.environment_id,
            },
        )
        return "Redeploy triggered successfully. Use railway_get_deployment_status to monitor progress."
    except RailwayAPIError as e:
        return f"Error triggering redeploy: {e}"


@mcp.tool(name="railway_restart_deployment")
async def restart_deployment(input: RestartDeploymentInput) -> str:
    """Restart a deployment without rebuilding. Useful for picking up new environment variables."""
    try:
        client = get_client()
        await client.execute(
            RESTART_DEPLOYMENT, {"id": input.deployment_id}
        )
        return "Deployment restarted successfully."
    except RailwayAPIError as e:
        return f"Error restarting deployment: {e}"
