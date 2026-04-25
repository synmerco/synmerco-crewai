"""MCP Server Adapter — connects to Synmerco's MCP endpoint.

Usage:
    from synmerco_crewai import get_synmerco_mcp_tools

    with get_synmerco_mcp_tools() as tools:
        agent = Agent(role="Buyer", tools=tools)

Requires: pip install synmerco-crewai[mcp]
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator


MCP_SSE_URL = "https://synmerco-escrow.onrender.com/mcp"


@contextmanager
def get_synmerco_mcp_tools(
    mcp_url: str | None = None,
) -> Generator[list, None, None]:
    """Connect to Synmerco's MCP server and return CrewAI-compatible tools.

    Uses CrewAI's built-in MCPServerAdapter to bridge MCP ↔ CrewAI.

    Args:
        mcp_url: Override the MCP SSE endpoint URL.

    Yields:
        List of CrewAI tools from the Synmerco MCP server.

    Requires:
        pip install synmerco-crewai[mcp]
    """
    try:
        from crewai_tools import MCPServerAdapter
    except ImportError:
        raise ImportError(
            "MCP support requires the mcp extra: "
            "pip install synmerco-crewai[mcp]"
        )

    url = mcp_url or os.environ.get("SYNMERCO_MCP_URL", MCP_SSE_URL)
    server_params = {"url": url}

    adapter = MCPServerAdapter(server_params)
    try:
        tools = adapter.tools
        yield tools
    finally:
        adapter.stop()
