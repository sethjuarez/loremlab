"""Azure AI Foundry service for agent management and execution."""

import os
import logging
import contextlib
from typing import AsyncGenerator

from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider

load_dotenv()

logger = logging.getLogger(__name__)

# Module-level cache for clients and credentials
_client_cache: dict[str, AIProjectClient] = {}
_credential_cache: DefaultAzureCredential | None = None

# Environment variable for project endpoint
FOUNDRY_PROJECT_ENV = "FOUNDRY_PROJECT"


def _get_project_url() -> str:
    """Get the project URL from environment variable.

    Returns:
        The FOUNDRY_PROJECT URL.

    Raises:
        ValueError: If FOUNDRY_PROJECT is not set.
    """
    project = os.getenv(FOUNDRY_PROJECT_ENV, "")
    if not project:
        raise ValueError(f"{FOUNDRY_PROJECT_ENV} environment variable is not set.")
    return f"https://{project}.services.ai.azure.com/api/projects/{project}"


def _get_openai_endpoint() -> str:
    """Derive the OpenAI endpoint from a project name.

    Returns:
        The OpenAI endpoint URL (without trailing slash).
    """
    project = os.getenv(FOUNDRY_PROJECT_ENV, "")
    if not project:
        raise ValueError(f"{FOUNDRY_PROJECT_ENV} environment variable is not set.")
    return f"https://{project}.openai.azure.com"


def get_cached_credential() -> DefaultAzureCredential:
    """Get or create a cached DefaultAzureCredential."""
    global _credential_cache
    if _credential_cache is None:
        _credential_cache = DefaultAzureCredential()
    return _credential_cache


def get_cached_client() -> AIProjectClient:
    """Get or create a cached AIProjectClient."""
    endpoint = _get_project_url()
    if endpoint not in _client_cache:
        credential = get_cached_credential()
        _client_cache[endpoint] = AIProjectClient(
            endpoint=endpoint,
            credential=credential,  # type: ignore[arg-type]
        )
    return _client_cache[endpoint]


@contextlib.asynccontextmanager
async def get_project_client() -> AsyncGenerator[AIProjectClient, None]:
    """Get an AIProjectClient context manager.

    Uses FOUNDRY_PROJECT environment variable.

    Yields:
        An AIProjectClient instance.
    """
    client = get_cached_client()

    try:
        yield client
    finally:
        # Don't close the client - it's cached and reused
        pass


async def get_openai_client(
    api_version: str = "2025-03-01-preview",
) -> AsyncAzureOpenAI:
    """Get an AsyncAzureOpenAI client with token authentication.

    Derives the OpenAI endpoint from FOUNDRY_PROJECT environment variable.

    Args:
        api_version: Azure OpenAI API version.

    Returns:
        An AsyncAzureOpenAI client configured for Azure AI Foundry.
    """
    endpoint = _get_openai_endpoint()

    logger.info(f"Creating OpenAI client for endpoint: {endpoint}")

    credential = get_cached_credential()
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )

    return AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        api_version=api_version,
    )
