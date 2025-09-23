"""Universal MCP tool wrappers for CrewAI services.

This module exposes a shared ``MCPToolsManager`` that coordinates the
lifecycle of the MCP gateway adapter and provides CrewAI compatible tool
wrappers for every tool advertised by the gateway.  The tools returned by
this module convert async MCP calls into synchronous executions using a
thread pool so they can be consumed seamlessly by CrewAI agents.
"""
from __future__ import annotations

import asyncio
import json
import time
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Type

import structlog
from app.services.mcp import MCPConfig, MCPGatewayAdapter, MCPToolFactory
from app.services.mcp.mcp_exceptions import MCPError
from app.services.mcp.mcp_crewai import BaseTool

try:  # pragma: no cover - optional dependency
    from pydantic import BaseModel, Field, create_model
except ImportError:  # pragma: no cover - fallback when Pydantic is unavailable
    class BaseModel:  # type: ignore[too-many-ancestors]
        """Fallback BaseModel stand-in when Pydantic is not installed."""

        pass

    def Field(**_: Any) -> None:
        return None

    def create_model(name: str, **fields: Any) -> Type[BaseModel]:
        return type(name, (BaseModel,), {})


LOGGER = structlog.get_logger(__name__)


class MCPToolsManagerError(RuntimeError):
    """Base exception for MCP tools manager issues."""


class MCPToolNotAvailableError(MCPToolsManagerError):
    """Raised when a requested MCP tool cannot be located."""


JSON_TYPE_MAPPING: Dict[str, Type[Any]] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}

LINKEDIN_RECOMMENDED_JOBS_TOOL_NAME = "MCP_DOCKER:get_recommended_jobs"
LINKEDIN_JOB_DETAILS_TOOL_NAME = "MCP_DOCKER:get_job_details"
DUCKDUCKGO_SEARCH_TOOL_NAME = "duckduckgo_search"
LINKEDIN_SEARCH_TOOL_NAME = "linkedin_search"
LINKEDIN_PROFILE_LOOKUP_TOOL_NAME = "profile_lookup"
LINKEDIN_COMPANY_PROFILE_TOOL_NAME = "linkedin_company_profile"
LINKEDIN_PERSON_PROFILE_TOOL_NAME = "linkedin_person_lookup"


class MCPGatewayTool(BaseTool):
    """CrewAI compatible wrapper around an MCP tool."""

    def __init__(self, manager: "MCPToolsManager", tool_name: str, tool_info: Dict[str, Any]):
        self._manager = manager
        self.tool_name = tool_info.get("name", tool_name)
        self._tool_info = dict(tool_info)

        description = self._tool_info.get("description", f"MCP tool: {self.tool_name}")
        args_schema = self._build_args_schema(self._tool_info.get("inputSchema"))

        super().__init__(
            name=self.tool_name,
            description=description,
            args_schema=args_schema,
        )

    @staticmethod
    def _json_type_to_python(json_type: str) -> Type[Any]:
        return JSON_TYPE_MAPPING.get(json_type, str)

    def _build_args_schema(self, schema: Optional[Dict[str, Any]]) -> Optional[Type[BaseModel]]:
        if not schema or not isinstance(schema, dict):
            return None

        properties: Dict[str, Dict[str, Any]] = schema.get("properties", {})
        required_fields: Sequence[str] = schema.get("required", [])

        if not properties:
            return None

        fields: Dict[str, Tuple[Type[Any], Any]] = {}
        for prop_name, prop_schema in properties.items():
            json_type = prop_schema.get("type", "string")
            python_type = self._json_type_to_python(json_type)
            description = prop_schema.get("description", "")

            if python_type is list:
                items_schema = prop_schema.get("items", {}) if isinstance(prop_schema, dict) else {}
                item_type = self._json_type_to_python(items_schema.get("type", "string"))
                python_type = List[item_type]  # type: ignore[index]

            if prop_name in required_fields:
                fields[prop_name] = (python_type, Field(description=description))
            else:
                fields[prop_name] = (Optional[python_type], Field(default=None, description=description))

        model_name = f"{self.tool_name.title().replace(':', '_').replace(' ', '')}Args"
        try:
            return create_model(model_name, **fields)
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning(
                "mcp_args_schema_build_failed",
                tool_name=self.tool_name,
                error=str(exc),
                error_type=exc.__class__.__name__,
            )
            return None

    def _run(self, **kwargs: Any) -> str:
        result = self._manager.execute_tool(self.tool_name, kwargs)
        try:
            return json.dumps(result, ensure_ascii=False, indent=2)
        except TypeError as exc:  # pragma: no cover - defensive
            LOGGER.warning(
                "mcp_tool_non_serializable_result",
                tool_name=self.tool_name,
                error=str(exc),
                error_type=exc.__class__.__name__,
            )
            return json.dumps({"success": False, "error": "Non-serializable result", "raw": str(result)})


class MCPToolsManager:
    """Manage MCP gateway connection and CrewAI tool wrappers."""

    def __init__(
        self,
        *,
        adapter: Optional[MCPGatewayAdapter] = None,
        max_workers: int = 4,
    ) -> None:
        self._adapter: Optional[MCPGatewayAdapter] = adapter
        self._factory: Optional[MCPToolFactory] = MCPToolFactory(adapter) if adapter else None
        self._lock = Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="mcp-tools")
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}
        self._tool_wrappers: Dict[str, MCPGatewayTool] = {}
        self._closed = False

    # ------------------------------------------------------------------
    # Core connection helpers
    # ------------------------------------------------------------------
    def _ensure_open(self) -> None:
        if self._closed:
            raise MCPToolsManagerError("MCPToolsManager has been closed")

    def _run_async(self, coroutine: "asyncio.Future[Any] | asyncio.Awaitable[Any]") -> Any:
        self._ensure_open()

        def _runner() -> Any:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(coroutine)
            finally:
                asyncio.set_event_loop(None)
                loop.close()

        future: Future[Any] = self._executor.submit(_runner)
        return future.result()

    def connect(self) -> MCPGatewayAdapter:
        """Ensure the MCP gateway adapter is connected and ready."""

        with self._lock:
            self._ensure_open()
            if self._adapter is None:
                try:
                    self._adapter = MCPConfig.from_environment()
                except Exception as exc:  # pragma: no cover - configuration errors are environment specific
                    raise MCPToolsManagerError(f"Failed to configure MCP adapter: {exc}") from exc

            adapter = self._adapter
            assert adapter is not None

            if not adapter.is_connected():
                try:
                    self._run_async(adapter.connect())
                except MCPError as exc:
                    raise MCPToolsManagerError(f"Failed to connect to MCP gateway: {exc}") from exc

            if self._factory is None:
                self._factory = MCPToolFactory(adapter)

            return adapter

    # ------------------------------------------------------------------
    # Tool discovery & caching
    # ------------------------------------------------------------------
    def list_tools(self, *, force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """Return metadata for all available MCP tools."""

        with self._lock:
            if self._tool_metadata and not force_refresh:
                return dict(self._tool_metadata)

        adapter = self.connect()

        try:
            metadata = self._run_async(adapter.list_tools())
        except MCPError as exc:
            raise MCPToolsManagerError(f"Failed to list MCP tools: {exc}") from exc

        with self._lock:
            self._tool_metadata = dict(metadata)

        return dict(metadata)

    def _match_tool_info(
        self,
        tool_name: str,
        *,
        aliases: Sequence[str] = (),
        refresh: bool = False,
    ) -> Dict[str, Any]:
        """Find tool metadata by name or alias."""

        tools = self.list_tools(force_refresh=refresh)
        candidates = (tool_name, *aliases)

        for candidate in candidates:
            if candidate in tools:
                return dict(tools[candidate])

        # Fallback: search aliases advertised in metadata
        candidate_set = {name for name in candidates if name}
        for info in tools.values():
            advertised_aliases = info.get("aliases") or []
            if any(alias in candidate_set for alias in advertised_aliases):
                return dict(info)

        raise MCPToolNotAvailableError(f"MCP tool not found: {tool_name}")

    def get_tool(
        self,
        tool_name: str,
        *,
        aliases: Sequence[str] = (),
    ) -> MCPGatewayTool:
        """Return (and cache) a CrewAI wrapper for the requested tool."""

        info = self._match_tool_info(tool_name, aliases=aliases)
        canonical_name = info.get("name", tool_name)

        with self._lock:
            wrapper = self._tool_wrappers.get(canonical_name)
            if wrapper is not None:
                return wrapper

            wrapper = MCPGatewayTool(self, canonical_name, info)
            self._tool_wrappers[canonical_name] = wrapper
            return wrapper

    def try_get_tool(self, tool_name: str, *, aliases: Sequence[str] = ()) -> Optional[MCPGatewayTool]:
        """Return a tool wrapper when available, otherwise ``None``."""

        try:
            return self.get_tool(tool_name, aliases=aliases)
        except MCPToolNotAvailableError:
            LOGGER.warning("mcp_tool_unavailable", tool_name=tool_name)
            return None

    def get_tools(
        self,
        tool_names: Sequence[str],
        *,
        alias_mapping: Optional[Dict[str, Sequence[str]]] = None,
    ) -> List[MCPGatewayTool]:
        """Retrieve a list of tool wrappers, skipping any unavailable ones."""

        wrappers: List[MCPGatewayTool] = []
        alias_mapping = alias_mapping or {}
        for name in tool_names:
            aliases = alias_mapping.get(name, tuple())
            tool = self.try_get_tool(name, aliases=aliases)
            if tool is not None:
                wrappers.append(tool)
        return wrappers

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool synchronously and return structured JSON."""

        start_time = time.perf_counter()
        argument_keys = tuple(sorted(arguments.keys()))

        try:
            adapter = self.connect()
        except MCPToolsManagerError as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            LOGGER.error(
                "mcp_connection_failed",
                tool_name=tool_name,
                duration_ms=duration_ms,
                argument_keys=argument_keys,
                error=str(exc),
                error_type=exc.__class__.__name__,
            )
            return {
                "success": False,
                "error": str(exc),
                "metadata": {"tool_name": tool_name, "arguments": arguments},
            }

        try:
            result = self._run_async(adapter.execute_tool(tool_name, arguments))
        except MCPError as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            LOGGER.error(
                "mcp_tool_execution_failed",
                tool_name=tool_name,
                duration_ms=duration_ms,
                argument_keys=argument_keys,
                error=str(exc),
                error_type=exc.__class__.__name__,
            )
            return {
                "success": False,
                "error": str(exc),
                "metadata": {"tool_name": tool_name, "arguments": arguments},
            }
        except Exception as exc:  # pragma: no cover - defensive guard
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            LOGGER.exception(
                "mcp_tool_execution_unexpected_error",
                tool_name=tool_name,
                duration_ms=duration_ms,
                argument_keys=argument_keys,
                error=str(exc),
                error_type=exc.__class__.__name__,
            )
            return {
                "success": False,
                "error": str(exc),
                "metadata": {"tool_name": tool_name, "arguments": arguments},
            }

        success_flag = True
        if isinstance(result, dict):
            if "success" in result:
                success_flag = bool(result.get("success"))

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        LOGGER.info(
            "mcp_tool_executed",
            tool_name=tool_name,
            duration_ms=duration_ms,
            argument_keys=argument_keys,
            success=bool(success_flag),
        )

        if isinstance(result, dict):
            return result

        return {
            "success": True,
            "data": result,
            "metadata": {"tool_name": tool_name, "arguments": arguments},
        }

    # ------------------------------------------------------------------
    # Lifecycle management
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Disconnect the adapter and release resources."""

        adapter: Optional[MCPGatewayAdapter]
        with self._lock:
            if self._closed:
                return
            adapter = self._adapter
            self._adapter = None
            self._factory = None
            self._tool_metadata.clear()
            self._tool_wrappers.clear()

        if adapter is not None and adapter.is_connected():
            try:
                self._run_async(adapter.disconnect())
            except MCPError as exc:
                LOGGER.warning(
                    "mcp_adapter_disconnect_failed",
                    error=str(exc),
                    error_type=exc.__class__.__name__,
                )
            except MCPToolsManagerError as exc:
                LOGGER.debug(
                    "mcp_tools_manager_closed_during_disconnect",
                    error=str(exc),
                    error_type=exc.__class__.__name__,
                )
            except RuntimeError:
                asyncio.run(adapter.disconnect())

        with self._lock:
            self._closed = True

        self._executor.shutdown(wait=True)

    def __enter__(self) -> "MCPToolsManager":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - context manager
        self.close()


class LinkedInRecommendedJobsTool(MCPGatewayTool):
    """Dedicated wrapper for LinkedIn recommended jobs retrieval."""

    def __init__(self, manager: MCPToolsManager):
        super().__init__(
            manager,
            LINKEDIN_RECOMMENDED_JOBS_TOOL_NAME,
            manager._match_tool_info(
                LINKEDIN_RECOMMENDED_JOBS_TOOL_NAME,
                aliases=("get_recommended_jobs",),
            ),
        )


class LinkedInJobDetailsTool(MCPGatewayTool):
    """Dedicated wrapper for LinkedIn job detail enrichment."""

    def __init__(self, manager: MCPToolsManager):
        super().__init__(
            manager,
            LINKEDIN_JOB_DETAILS_TOOL_NAME,
            manager._match_tool_info(
                LINKEDIN_JOB_DETAILS_TOOL_NAME,
                aliases=("get_job_details",),
            ),
        )


class DuckDuckGoSearchTool(MCPGatewayTool):
    """Wrapper around the DuckDuckGo MCP web search tool."""

    def __init__(self, manager: MCPToolsManager):
        super().__init__(manager, DUCKDUCKGO_SEARCH_TOOL_NAME, manager._match_tool_info(DUCKDUCKGO_SEARCH_TOOL_NAME))


class LinkedInSearchTool(MCPGatewayTool):
    """Wrapper around LinkedIn search MCP tool."""

    def __init__(self, manager: MCPToolsManager):
        super().__init__(manager, LINKEDIN_SEARCH_TOOL_NAME, manager._match_tool_info(LINKEDIN_SEARCH_TOOL_NAME))


class LinkedInProfileLookupTool(MCPGatewayTool):
    """Wrapper for LinkedIn person profile lookups."""

    def __init__(self, manager: MCPToolsManager):
        super().__init__(
            manager,
            LINKEDIN_PROFILE_LOOKUP_TOOL_NAME,
            manager._match_tool_info(
                LINKEDIN_PROFILE_LOOKUP_TOOL_NAME,
                aliases=("linkedin_profile_lookup", "person_lookup"),
            ),
        )


class LinkedInCompanyProfileTool(MCPGatewayTool):
    """Wrapper for LinkedIn company profile enrichment."""

    def __init__(self, manager: MCPToolsManager):
        super().__init__(
            manager,
            LINKEDIN_COMPANY_PROFILE_TOOL_NAME,
            manager._match_tool_info(
                LINKEDIN_COMPANY_PROFILE_TOOL_NAME,
                aliases=("company_profile_lookup", "linkedin_company_lookup"),
            ),
        )


class LinkedInPersonProfileTool(MCPGatewayTool):
    """Wrapper for LinkedIn person profile enrichment."""

    def __init__(self, manager: MCPToolsManager):
        super().__init__(
            manager,
            LINKEDIN_PERSON_PROFILE_TOOL_NAME,
            manager._match_tool_info(
                LINKEDIN_PERSON_PROFILE_TOOL_NAME,
                aliases=("linkedin_person_lookup", "person_profile_lookup"),
            ),
        )


__all__ = [
    "MCPGatewayTool",
    "MCPToolsManager",
    "MCPToolsManagerError",
    "MCPToolNotAvailableError",
    "LinkedInRecommendedJobsTool",
    "LinkedInJobDetailsTool",
    "DuckDuckGoSearchTool",
    "LinkedInSearchTool",
    "LinkedInProfileLookupTool",
    "LinkedInCompanyProfileTool",
    "LinkedInPersonProfileTool",
    "LINKEDIN_RECOMMENDED_JOBS_TOOL_NAME",
    "LINKEDIN_JOB_DETAILS_TOOL_NAME",
    "DUCKDUCKGO_SEARCH_TOOL_NAME",
    "LINKEDIN_SEARCH_TOOL_NAME",
    "LINKEDIN_PROFILE_LOOKUP_TOOL_NAME",
    "LINKEDIN_COMPANY_PROFILE_TOOL_NAME",
    "LINKEDIN_PERSON_PROFILE_TOOL_NAME",
]
