"""CrewAI BaseTool factory with Python 3.14 compat shim."""

from __future__ import annotations

import json
from typing import Any, Optional, Type

from pydantic import BaseModel, Field

try:
    from crewai.tools import BaseTool as _CrewAIBaseTool
    _CREWAI_AVAILABLE = True
except ImportError:
    _CREWAI_AVAILABLE = False

    class _CrewAIBaseTool(BaseModel):
        name: str = ""
        description: str = ""
        args_schema: Any = None

        def _run(self, **kwargs):
            raise NotImplementedError

        def run(self, **kwargs):
            return self._run(**kwargs)

BaseTool = _CrewAIBaseTool

from synmerco_crewai._client import (
    SynmercoHTTPClient, SynmercoAPIError,
    validate_did, validate_amount, validate_sha256,
)
from synmerco_crewai._registry import TOOLS


def _build_schema(tool_def: dict) -> Type[BaseModel]:
    fields_def = tool_def.get("fields", {})
    required = set(tool_def.get("required", []))
    annotations: dict[str, Any] = {}
    namespace: dict[str, Any] = {}
    for fname, fmeta in fields_def.items():
        ftype = fmeta.get("type", "str")
        desc = fmeta.get("description", fname)
        is_req = fname in required
        if ftype == "did":
            annotations[fname] = str if is_req else Optional[str]
            namespace[fname] = Field(..., description=desc, min_length=8, max_length=256) if is_req else Field(None, description=desc)
        elif ftype == "amount":
            annotations[fname] = int if is_req else Optional[int]
            namespace[fname] = Field(..., description=desc, ge=100, le=10_000_000) if is_req else Field(None, description=desc)
        elif ftype == "sha256":
            annotations[fname] = str if is_req else Optional[str]
            namespace[fname] = Field(..., description=desc, min_length=64, max_length=64) if is_req else Field(None, description=desc)
        elif ftype == "int":
            annotations[fname] = int if is_req else Optional[int]
            namespace[fname] = Field(..., description=desc) if is_req else Field(None, description=desc)
        elif ftype == "str_array":
            annotations[fname] = list[str] if is_req else Optional[list[str]]
            namespace[fname] = Field(..., description=desc, min_length=1) if is_req else Field(None, description=desc)
        else:
            annotations[fname] = str if is_req else Optional[str]
            namespace[fname] = Field(..., description=desc) if is_req else Field(None, description=desc)
    namespace["__annotations__"] = annotations
    schema_name = "".join(p.capitalize() for p in tool_def["name"].split("_")) + "Input"
    return type(schema_name, (BaseModel,), namespace)


def _build_tool_class(tool_def: dict, http: SynmercoHTTPClient) -> Type[BaseTool]:
    schema_cls = _build_schema(tool_def)
    tool_name = tool_def["name"]
    tool_desc = tool_def["description"]
    method = tool_def["method"]
    path_template = tool_def["path"]
    path_params = set(tool_def.get("path_params", []))

    class SynmercoCrewTool(BaseTool):
        name: str = tool_name
        description: str = tool_desc
        args_schema: Type[BaseModel] = schema_cls

        def _run(self, **kwargs: Any) -> str:
            for fn, fm in tool_def.get("fields", {}).items():
                v = kwargs.get(fn)
                if v is None: continue
                ft = fm.get("type", "str")
                if ft == "did": kwargs[fn] = validate_did(v)
                elif ft == "amount": kwargs[fn] = validate_amount(v)
                elif ft == "sha256": kwargs[fn] = validate_sha256(v)
            path = path_template
            for pp in path_params:
                path = path.replace("{" + pp + "}", str(kwargs.pop(pp, "")))
            try:
                if method == "GET":
                    result = http.get(path, **kwargs)
                else:
                    result = http.post(path, kwargs)
                return json.dumps(result, indent=2, default=str)
            except SynmercoAPIError as e:
                return f"Synmerco API error: {e}"
            except Exception as e:
                return f"Error calling {tool_name}: {e}"

    SynmercoCrewTool.__name__ = "".join(p.capitalize() for p in tool_name.split("_")) + "Tool"
    SynmercoCrewTool.__qualname__ = SynmercoCrewTool.__name__
    return SynmercoCrewTool


def build_all_tools(api_key=None, base_url=None, timeout=30.0, include_free_only=False):
    http = SynmercoHTTPClient(api_key=api_key, base_url=base_url, timeout=timeout)
    tools = []
    for tdef in TOOLS:
        if include_free_only and tdef.get("auth", True): continue
        cls = _build_tool_class(tdef, http)
        tools.append(cls())
    return tools


def is_crewai_available() -> bool:
    return _CREWAI_AVAILABLE
