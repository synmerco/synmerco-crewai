"""synmerco-crewai — 46 CrewAI tools for AI agent commerce.

Two ways to use:

1. Direct tools (recommended):
    from synmerco_crewai import get_synmerco_tools
    tools = get_synmerco_tools(api_key="your_key")

2. MCP adapter (requires synmerco-crewai[mcp]):
    from synmerco_crewai import get_synmerco_mcp_tools
    with get_synmerco_mcp_tools() as tools:
        agent = Agent(tools=tools)
"""

from synmerco_crewai._factory import build_all_tools
from synmerco_crewai._client import SynmercoHTTPClient, SynmercoAPIError

__version__ = "1.0.0"
__all__ = [
    "get_synmerco_tools",
    "get_synmerco_mcp_tools",
    "SynmercoHTTPClient",
    "SynmercoAPIError",
]


def get_synmerco_tools(
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: float = 30.0,
    include_free_only: bool = False,
):
    """Get all 46 Synmerco tools as CrewAI BaseTool instances.

    Args:
        api_key: Your Synmerco API key. Also reads SYNMERCO_API_KEY env var.
        base_url: Override the API URL.
        timeout: HTTP timeout in seconds (default: 30).
        include_free_only: If True, returns only free tools.

    Returns:
        List of CrewAI BaseTool instances.

    Example:
        >>> tools = get_synmerco_tools(api_key="sk_live_...")
        >>> len(tools)
        46
    """
    return build_all_tools(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        include_free_only=include_free_only,
    )


def get_synmerco_mcp_tools(mcp_url: str | None = None):
    """Connect to Synmerco's MCP server via CrewAI's MCPServerAdapter.

    Use as a context manager:
        with get_synmerco_mcp_tools() as tools:
            agent = Agent(tools=tools)

    Requires: pip install synmerco-crewai[mcp]
    """
    from synmerco_crewai._mcp_adapter import get_synmerco_mcp_tools as _get
    return _get(mcp_url=mcp_url)
