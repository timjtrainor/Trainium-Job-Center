"""Utility script to verify manual MCP Gateway SSE handshake."""

import argparse
import asyncio
from typing import Optional
from urllib.parse import parse_qs, urljoin, urlparse

import httpx


def _normalize_session_key(name: Optional[str]) -> str:
    if not name:
        return ""
    return name.strip().lower().replace("_", "").replace("-", "")


def _extract_session_details(gateway_url: str, response: httpx.Response) -> tuple[str, str]:
    """Resolve the SSE endpoint URL and session ID from a gateway response."""

    if response.status_code == 307:
        location = response.headers.get("location")
        if not location:
            raise RuntimeError("Gateway redirect did not include a Location header")
        endpoint = (
            urljoin(f"{gateway_url}/", location.lstrip("/"))
            if location.startswith("/")
            else location
        )
    elif response.status_code == 200:
        try:
            payload = response.json()
        except ValueError as exc:  # pragma: no cover - defensive
            raise RuntimeError(f"Failed to decode JSON body: {exc}") from exc
        endpoint_hint = payload.get("endpoint")
        if not endpoint_hint:
            raise RuntimeError("Gateway response missing 'endpoint' value")
        endpoint = (
            urljoin(f"{gateway_url}/", endpoint_hint.lstrip("/"))
            if str(endpoint_hint).startswith("/")
            else str(endpoint_hint)
        )
    else:
        response.raise_for_status()
        raise RuntimeError(
            f"Unexpected session allocation status: {response.status_code}"
        )

    parsed = urlparse(endpoint)
    query_params = parse_qs(parsed.query)
    normalized = {
        _normalize_session_key(key): value for key, value in query_params.items()
    }
    session_id = normalized.get("sessionid", [None])[0]
    if not session_id:
        raise RuntimeError("SSE endpoint did not include a sessionid query parameter")

    return endpoint, session_id


async def _open_event_stream(client: httpx.AsyncClient, endpoint: str, max_events: int) -> None:
    """Stream SSE events and print them to stdout."""

    event_lines: list[str] = []
    event_count = 0

    async with client.stream("GET", endpoint, headers={"Accept": "text/event-stream"}) as stream:
        async for line in stream.aiter_lines():
            if line is None:
                continue
            if line == "":
                if not event_lines:
                    continue
                event_type = "message"
                data_lines: list[str] = []
                for entry in event_lines:
                    if entry.startswith("event:"):
                        event_type = entry[len("event:") :].strip() or event_type
                    elif entry.startswith("data:"):
                        data_lines.append(entry[len("data:") :].lstrip())
                    else:
                        data_lines.append(entry)
                payload = "\n".join(data_lines)
                print(f"[{event_type}] {payload}")
                event_lines.clear()
                event_count += 1
                if max_events and event_count >= max_events:
                    print("Reached maximum event count; stopping stream.")
                    break
                continue

            event_lines.append(line)


async def main(gateway_url: str, server_name: str, max_events: int) -> None:
    """Execute the manual session handshake and print SSE events."""

    base_url = gateway_url.rstrip("/")
    async with httpx.AsyncClient(follow_redirects=False, timeout=None) as client:
        print(f"Creating new session for {server_name}…")
        session_response = await client.get(f"{base_url}/sse")
        endpoint, session_id = _extract_session_details(base_url, session_response)
        print(f"Allocated sessionid={session_id}")
        print(f"Attaching server {server_name} to session {session_id}…")
        attach_response = await client.post(
            f"{base_url}/servers/{server_name}/connect",
            params={"sessionid": session_id},
        )
        attach_response.raise_for_status()
        print(f"Establishing SSE stream at {endpoint}")
        await _open_event_stream(client, endpoint, max_events)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify manual SSE handshake with the MCP Gateway"
    )
    parser.add_argument(
        "--gateway",
        default="http://localhost:8811",
        help="Base URL of the MCP Gateway (default: http://localhost:8811)",
    )
    parser.add_argument(
        "--server",
        required=True,
        help="MCP server name to attach (e.g. duckduckgo)",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=0,
        help="Optional limit for the number of SSE events to print (0 means stream indefinitely)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        asyncio.run(main(args.gateway, args.server, args.max_events))
    except KeyboardInterrupt:
        print("Stream interrupted by user.")
