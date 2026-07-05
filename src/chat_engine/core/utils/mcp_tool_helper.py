import asyncio
import json
import shutil
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolResult, TextContent

from chat_engine.core.config.logging import logger


def save_reservation_snapshot_via_mcp(
    reservation_data: dict[str, Any],
    base_directory: str = "data/reservations",
) -> dict[str, Any]:
    """Persist reservation data into a daily JSON file path using Filesystem MCP.

    Output format:
            data/reservations/YYYY-MM-DD/<reservation_id>.json
    """
    reservation_id = reservation_data.get("reservation_id")
    if not reservation_id:
        raise ValueError("reservation_data must contain a non-empty 'reservation_id'.")

    base_path = Path(base_directory)
    if not base_path.is_absolute():
        base_path = (Path.cwd() / base_path).resolve()

    base_path.mkdir(parents=True, exist_ok=True)
    day = datetime.now(UTC).date()
    file_path = base_path / day.isoformat() / f"{reservation_id}.json"

    logger.info(f"Persisting reservation snapshot with MCP for reservation_id: {reservation_id}")
    return _run_async(_write_file_with_mcp(file_path=file_path, payload=reservation_data, allowed_root=base_path))


async def _write_file_with_mcp(file_path: Path, payload: dict[str, Any], allowed_root: Path) -> dict[str, Any]:
    """Write a JSON object to a file by invoking Filesystem MCP's write_file tool."""
    file_content = json.dumps(payload, indent=2, ensure_ascii=True, default=str)

    try:
        server_params = _build_server_params(allowed_root)
        async with stdio_client(server_params) as (read_stream, write_stream):
            session = ClientSession(read_stream, write_stream)
            async with session:
                await session.initialize()
                # Ensure daily directory exists before writing the file
                create_dir_result = await session.call_tool(
                    "create_directory", {"path": str(file_path.parent.resolve())}
                )
                if create_dir_result.isError:
                    error_text = _extract_tool_text(create_dir_result)
                    raise RuntimeError(f"Failed to create destination directory via MCP: {error_text}")
                # Write the reservation snapshot to the specified file path
                write_result = await session.call_tool(
                    name="write_file",
                    arguments={
                        "path": str(file_path.resolve()),
                        "content": file_content,
                    },
                )
                if write_result.isError:
                    error_text = _extract_tool_text(write_result)
                    raise RuntimeError(f"Failed to write reservation file via MCP: {error_text}")

                logger.info(f"Reservation snapshot persisted via MCP to: {file_path}")
                return {"path": str(file_path), "written": True, "tool_output": _extract_tool_text(write_result)}
    except Exception as e:
        logger.error(
            "MCP filesystem write failed. This often means the Filesystem MCP process could not start "
            f"or exited early (e.g. missing npx / invalid allowed directory). Error: {e}"
        )
        raise RuntimeError(
            "Failed to initialize or use Filesystem MCP server. Verify Node.js/npx is installed and "
            "the allowed directory is valid."
        ) from e


def _run_async(coroutine):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)

    with ThreadPoolExecutor(max_workers=1) as executor:
        outcome: Future[Any] = executor.submit(asyncio.run, coroutine)
        return outcome.result()


def _build_server_params(allowed_root: Path) -> StdioServerParameters:
    """Build stdio server parameters for Filesystem MCP server."""
    npx_cmd = shutil.which("npx.cmd") or shutil.which("npx")
    if not npx_cmd:
        raise RuntimeError("npx executable was not found. Install Node.js (which includes npm/npx), then retry.")

    args = ["/c", npx_cmd, "-y", "@modelcontextprotocol/server-filesystem"]
    args.append(str(allowed_root.resolve()))
    return StdioServerParameters(command="cmd", args=args, cwd=str(Path.cwd()))


def _extract_tool_text(result: CallToolResult) -> str:
    """Extract text content from a generic MCP tool result."""
    return "\n".join(item.text for item in result.content if isinstance(item, TextContent))
