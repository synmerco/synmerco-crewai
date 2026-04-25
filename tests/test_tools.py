"""Tests for synmerco-crewai package."""

import pytest
from synmerco_crewai import get_synmerco_tools
from synmerco_crewai._client import (
    validate_did, validate_amount, validate_sha256,
    SynmercoHTTPClient, SynmercoAPIError,
)
from synmerco_crewai._registry import TOOLS


# ─── Registry ────────────────────────────────────────────────

def test_registry_has_46_tools():
    assert len(TOOLS) >= 44

def test_no_duplicate_names():
    names = [t["name"] for t in TOOLS]
    assert len(names) == len(set(names))

def test_all_tools_have_required_keys():
    for t in TOOLS:
        assert "name" in t
        assert "description" in t
        assert "method" in t
        assert "path" in t
        assert t["method"] in ("GET", "POST")

def test_free_tools_count():
    free = [t for t in TOOLS if not t.get("auth", True)]
    assert len(free) >= 6


# ─── Validation ──────────────────────────────────────────────

def test_validate_did_valid():
    assert validate_did("did:key:z6MkTest123") == "did:key:z6MkTest123"

def test_validate_did_rejects_garbage():
    with pytest.raises(ValueError):
        validate_did("garbage")

def test_validate_amount_range():
    assert validate_amount(500) == 500
    with pytest.raises(ValueError):
        validate_amount(10)
    with pytest.raises(ValueError):
        validate_amount(99_999_999)

def test_validate_sha256():
    assert validate_sha256("ab" * 32) == "ab" * 32
    with pytest.raises(ValueError):
        validate_sha256("short")


# ─── Tool Factory ────────────────────────────────────────────

def test_tools_return_list():
    tools = get_synmerco_tools(include_free_only=True)
    assert isinstance(tools, list)
    assert len(tools) >= 6

def test_tools_have_name_desc_schema():
    tools = get_synmerco_tools(api_key="test")
    for t in tools:
        assert t.name
        assert t.description
        assert len(t.description) > 20
        assert t.args_schema is not None

def test_free_tools_include_expected():
    tools = get_synmerco_tools(include_free_only=True)
    names = {t.name for t in tools}
    assert "lookup_trust_score" in names
    assert "search_agents" in names
    assert "estimate_fees" in names


# ─── Client ──────────────────────────────────────────────────

def test_client_defaults():
    c = SynmercoHTTPClient()
    assert "synmerco" in c.base_url

def test_client_custom():
    c = SynmercoHTTPClient(api_key="k", base_url="https://x.com")
    assert c.api_key == "k"
    assert c.base_url == "https://x.com"

def test_error_formatting():
    e = SynmercoAPIError(403, "forbidden", "No access")
    assert "403" in str(e)
    assert "forbidden" in str(e)


# ─── MCP Adapter ─────────────────────────────────────────────

def test_mcp_import_without_extras():
    """get_synmerco_mcp_tools should be importable even without [mcp] extras."""
    from synmerco_crewai import get_synmerco_mcp_tools
    assert callable(get_synmerco_mcp_tools)
