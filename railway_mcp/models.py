"""Pydantic input models for Railway MCP tools."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from enum import Enum


class ResponseFormat(str, Enum):
    markdown = "markdown"
    json = "json"


class BaseInput(BaseModel):
    """Shared config for all input models."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.markdown,
        description="Output format: 'markdown' for human-readable, 'json' for structured data",
    )


# -- Projects -----------------------------------------------------------------


class ListProjectsInput(BaseInput):
    """Input for listing all Railway projects."""

    pass


class GetProjectInput(BaseInput):
    """Input for fetching a single project by ID."""

    project_id: str = Field(
        ...,
        description="Railway project ID (UUID). Use railway_list_projects to find it.",
        min_length=1,
    )


# -- Services -----------------------------------------------------------------


class ListServicesInput(BaseInput):
    """Input for listing services in a project."""

    project_id: str = Field(
        ...,
        description="Railway project ID (UUID)",
        min_length=1,
    )


class GetServiceInput(BaseInput):
    """Input for getting service config in a specific environment."""

    service_id: str = Field(
        ...,
        description="Railway service ID (UUID)",
        min_length=1,
    )
    environment_id: str = Field(
        ...,
        description="Railway environment ID (UUID)",
        min_length=1,
    )


# -- Environments -------------------------------------------------------------


class ListEnvironmentsInput(BaseInput):
    """Input for listing environments in a project."""

    project_id: str = Field(
        ...,
        description="Railway project ID (UUID)",
        min_length=1,
    )


class CreateEnvironmentInput(BaseInput):
    """Input for creating a new environment."""

    project_id: str = Field(
        ...,
        description="Railway project ID (UUID)",
        min_length=1,
    )
    name: str = Field(
        ...,
        description="Name for the new environment (e.g. 'staging', 'dev')",
        min_length=1,
        max_length=64,
    )
    ephemeral: bool = Field(
        default=False,
        description="If true, creates a temporary PR-style environment",
    )


class DuplicateEnvironmentInput(BaseInput):
    """Input for duplicating an existing environment."""

    project_id: str = Field(
        ...,
        description="Railway project ID (UUID)",
        min_length=1,
    )
    source_environment_id: str = Field(
        ...,
        description="ID of the environment to duplicate",
        min_length=1,
    )
    name: str = Field(
        ...,
        description="Name for the duplicated environment",
        min_length=1,
        max_length=64,
    )


# -- Variables ----------------------------------------------------------------


class ListVariablesInput(BaseInput):
    """Input for listing variables on a service or environment."""

    project_id: str = Field(
        ...,
        description="Railway project ID (UUID)",
        min_length=1,
    )
    environment_id: str = Field(
        ...,
        description="Railway environment ID (UUID)",
        min_length=1,
    )
    service_id: Optional[str] = Field(
        default=None,
        description="Service ID. If omitted, returns shared/environment-level variables.",
    )


class GetVariablesUnresolvedInput(BaseInput):
    """Input for fetching variables with template references intact."""

    project_id: str = Field(
        ...,
        description="Railway project ID (UUID)",
        min_length=1,
    )
    environment_id: str = Field(
        ...,
        description="Railway environment ID (UUID)",
        min_length=1,
    )
    service_id: Optional[str] = Field(
        default=None,
        description="Service ID. If omitted, returns shared variables.",
    )


class SetVariableInput(BaseInput):
    """Input for setting a single variable."""

    project_id: str = Field(
        ...,
        description="Railway project ID (UUID)",
        min_length=1,
    )
    environment_id: str = Field(
        ...,
        description="Railway environment ID (UUID)",
        min_length=1,
    )
    name: str = Field(
        ...,
        description="Variable name (e.g. 'DATABASE_URL', 'SECRET_KEY')",
        min_length=1,
    )
    value: str = Field(
        ...,
        description="Variable value",
    )
    service_id: Optional[str] = Field(
        default=None,
        description="Service ID. If omitted, sets a shared/environment variable.",
    )


class BulkSetVariablesInput(BaseInput):
    """Input for setting multiple variables at once."""

    project_id: str = Field(
        ...,
        description="Railway project ID (UUID)",
        min_length=1,
    )
    environment_id: str = Field(
        ...,
        description="Railway environment ID (UUID)",
        min_length=1,
    )
    variables: dict[str, str] = Field(
        ...,
        description="Key-value dict of variables to set (e.g. {'KEY': 'value', 'OTHER': 'val2'})",
    )
    service_id: Optional[str] = Field(
        default=None,
        description="Service ID. If omitted, sets shared/environment variables.",
    )
    replace: bool = Field(
        default=False,
        description=(
            "WARNING: If true, all existing variables NOT in this dict will be DELETED. "
            "Use with extreme caution. Default false (merge/upsert only)."
        ),
    )


class DeleteVariableInput(BaseInput):
    """Input for deleting a single variable."""

    project_id: str = Field(
        ...,
        description="Railway project ID (UUID)",
        min_length=1,
    )
    environment_id: str = Field(
        ...,
        description="Railway environment ID (UUID)",
        min_length=1,
    )
    name: str = Field(
        ...,
        description="Name of the variable to delete",
        min_length=1,
    )
    service_id: Optional[str] = Field(
        default=None,
        description="Service ID. If omitted, deletes a shared variable.",
    )


# -- Deployments --------------------------------------------------------------


class GetDeploymentStatusInput(BaseInput):
    """Input for checking the latest deployment status."""

    project_id: str = Field(
        ...,
        description="Railway project ID (UUID)",
        min_length=1,
    )
    environment_id: str = Field(
        ...,
        description="Railway environment ID (UUID)",
        min_length=1,
    )
    service_id: str = Field(
        ...,
        description="Railway service ID (UUID)",
        min_length=1,
    )


class GetBuildLogsInput(BaseInput):
    """Input for fetching build logs."""

    deployment_id: str = Field(
        ...,
        description="Deployment ID (get from railway_get_deployment_status)",
        min_length=1,
    )


class GetDeployLogsInput(BaseInput):
    """Input for fetching runtime/deploy logs."""

    deployment_id: str = Field(
        ...,
        description="Deployment ID (get from railway_get_deployment_status)",
        min_length=1,
    )


class RedeployInput(BaseInput):
    """Input for redeploying a service (full rebuild)."""

    service_id: str = Field(
        ...,
        description="Railway service ID (UUID)",
        min_length=1,
    )
    environment_id: str = Field(
        ...,
        description="Railway environment ID (UUID)",
        min_length=1,
    )


class RestartDeploymentInput(BaseInput):
    """Input for restarting a deployment without rebuilding."""

    deployment_id: str = Field(
        ...,
        description="Deployment ID to restart",
        min_length=1,
    )
