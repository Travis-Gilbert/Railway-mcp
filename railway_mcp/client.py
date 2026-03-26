"""Async GraphQL client for the Railway public API."""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

RAILWAY_GQL_ENDPOINT = "https://backboard.railway.app/graphql/v2"


class RailwayAPIError(Exception):
    """Raised when the Railway GraphQL API returns an error."""

    def __init__(self, message: str, errors: list | None = None):
        super().__init__(message)
        self.errors = errors or []


class RailwayClient:
    """Async client for Railway's GraphQL v2 API."""

    def __init__(self, token: str | None = None):
        resolved_token = token or os.environ.get("RAILWAY_API_TOKEN", "")
        if not resolved_token:
            raise RailwayAPIError(
                "No Railway API token found. Set RAILWAY_API_TOKEN in your "
                "environment or pass it directly. Generate one at "
                "https://railway.com/account/tokens"
            )
        self._client = httpx.AsyncClient(
            base_url=RAILWAY_GQL_ENDPOINT,
            headers={
                "Authorization": f"Bearer {resolved_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def execute(
        self, query: str, variables: dict | None = None
    ) -> dict:
        """Execute a GraphQL query/mutation and return the data payload.

        Raises RailwayAPIError on GraphQL-level errors or HTTP failures.
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            resp = await self._client.post("", json=payload)
        except httpx.TimeoutException:
            raise RailwayAPIError(
                "Request to Railway API timed out. Try again in a moment."
            )
        except httpx.ConnectError:
            raise RailwayAPIError(
                "Could not connect to Railway API at "
                f"{RAILWAY_GQL_ENDPOINT}. Check your network."
            )

        if resp.status_code == 401:
            raise RailwayAPIError(
                "Railway API token is invalid or expired. Generate a new "
                "one at https://railway.com/account/tokens"
            )
        if resp.status_code == 403:
            raise RailwayAPIError(
                "Forbidden. Your token may not have access to this resource."
            )
        if resp.status_code == 429:
            raise RailwayAPIError(
                "Rate limited by Railway API. Try again in a moment."
            )

        resp.raise_for_status()

        data = resp.json()
        if "errors" in data:
            messages = "; ".join(
                e.get("message", "Unknown error") for e in data["errors"]
            )
            raise RailwayAPIError(messages, errors=data["errors"])

        return data.get("data", {})

    async def close(self):
        """Close the underlying HTTP client."""
        await self._client.aclose()


# Module-level singleton, lazily initialized
_client: RailwayClient | None = None


def get_client() -> RailwayClient:
    """Get or create the module-level Railway client singleton."""
    global _client
    if _client is None:
        _client = RailwayClient()
    return _client
