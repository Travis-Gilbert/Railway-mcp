"""GraphQL queries and mutations for the Railway API.

All strings are constants. Variables are passed separately via the
client.execute(query, variables) interface.
"""

# -- Projects -----------------------------------------------------------------

LIST_PROJECTS = """
query listProjects {
  projects {
    edges {
      node {
        id
        name
        description
        createdAt
        environments {
          edges {
            node {
              id
              name
            }
          }
        }
        services {
          edges {
            node {
              id
              name
              icon
            }
          }
        }
      }
    }
  }
}
"""

GET_PROJECT = """
query project($id: String!) {
  project(id: $id) {
    id
    name
    description
    createdAt
    environments {
      edges {
        node {
          id
          name
        }
      }
    }
    services {
      edges {
        node {
          id
          name
          icon
        }
      }
    }
  }
}
"""

# -- Services -----------------------------------------------------------------

GET_SERVICE = """
query service($id: String!) {
  service(id: $id) {
    id
    name
    icon
    createdAt
    projectId
  }
}
"""

GET_SERVICE_INSTANCE = """
query serviceInstance($serviceId: String!, $environmentId: String!) {
  serviceInstance(serviceId: $serviceId, environmentId: $environmentId) {
    id
    serviceName
    startCommand
    buildCommand
    rootDirectory
    healthcheckPath
    region
    numReplicas
    restartPolicyType
    restartPolicyMaxRetries
    latestDeployment {
      id
      status
      createdAt
    }
  }
}
"""

SERVICE_CREATE = """
mutation serviceCreate($input: ServiceCreateInput!) {
  serviceCreate(input: $input) {
    id
    name
  }
}
"""

SERVICE_DELETE = """
mutation serviceDelete($id: String!) {
  serviceDelete(id: $id)
}
"""

SERVICE_CONNECT = """
mutation serviceConnect($id: String!, $input: ServiceConnectInput!) {
  serviceConnect(id: $id, input: $input) {
    id
  }
}
"""

SERVICE_DISCONNECT = """
mutation serviceDisconnect($id: String!) {
  serviceDisconnect(id: $id) {
    id
  }
}
"""

SERVICE_INSTANCE_UPDATE = """
mutation serviceInstanceUpdate(
  $serviceId: String!
  $environmentId: String!
  $input: ServiceInstanceUpdateInput!
) {
  serviceInstanceUpdate(
    serviceId: $serviceId
    environmentId: $environmentId
    input: $input
  )
}
"""

# -- Environments -------------------------------------------------------------

LIST_ENVIRONMENTS = """
query environments($projectId: String!) {
  project(id: $projectId) {
    environments {
      edges {
        node {
          id
          name
        }
      }
    }
  }
}
"""

CREATE_ENVIRONMENT = """
mutation environmentCreate($input: EnvironmentCreateInput!) {
  environmentCreate(input: $input) {
    id
    name
  }
}
"""

# -- Variables ----------------------------------------------------------------

GET_VARIABLES = """
query variables(
  $projectId: String!
  $environmentId: String!
  $serviceId: String
) {
  variables(
    projectId: $projectId
    environmentId: $environmentId
    serviceId: $serviceId
  )
}
"""

GET_VARIABLES_FOR_SERVICE_INSTANCE = """
query variablesForServiceInstance(
  $projectId: String!
  $environmentId: String!
  $serviceId: String
) {
  variablesForServiceInstance(
    projectId: $projectId
    environmentId: $environmentId
    serviceId: $serviceId
  )
}
"""

UPSERT_VARIABLE = """
mutation variableUpsert($input: VariableUpsertInput!) {
  variableUpsert(input: $input)
}
"""

UPSERT_VARIABLE_COLLECTION = """
mutation variableCollectionUpsert($input: VariableCollectionUpsertInput!) {
  variableCollectionUpsert(input: $input)
}
"""

DELETE_VARIABLE = """
mutation variableDelete($input: VariableDeleteInput!) {
  variableDelete(input: $input)
}
"""

# -- Deployments --------------------------------------------------------------

LIST_DEPLOYMENTS = """
query deployments(
  $projectId: String!
  $environmentId: String!
  $serviceId: String!
  $first: Int
) {
  deployments(
    first: $first
    input: {
      projectId: $projectId
      environmentId: $environmentId
      serviceId: $serviceId
    }
  ) {
    edges {
      node {
        id
        status
        staticUrl
        createdAt
        canRollback
      }
    }
  }
}
"""

GET_BUILD_LOGS = """
query buildLogs($deploymentId: String!) {
  buildLogs(deploymentId: $deploymentId) {
    message
    timestamp
    severity
  }
}
"""

GET_DEPLOY_LOGS = """
query deploymentLogs($deploymentId: String!) {
  deploymentLogs(deploymentId: $deploymentId) {
    message
    timestamp
    severity
  }
}
"""

REDEPLOY_SERVICE = """
mutation serviceInstanceRedeploy(
  $serviceId: String!
  $environmentId: String!
) {
  serviceInstanceRedeploy(
    serviceId: $serviceId
    environmentId: $environmentId
  )
}
"""

DEPLOY_SERVICE = """
mutation serviceInstanceDeployV2(
  $serviceId: String!
  $environmentId: String!
) {
  serviceInstanceDeployV2(
    serviceId: $serviceId
    environmentId: $environmentId
  )
}
"""

RESTART_DEPLOYMENT = """
mutation deploymentRestart($id: String!) {
  deploymentRestart(id: $id)
}
"""
