from __future__ import annotations

from datetime import timedelta

import anyio

from mcp.client.session import ClientSession

import server as mcp_server


async def main() -> None:
    print("Starting MCP stdio client...", flush=True)
    client_to_server_send, client_to_server_recv = anyio.create_memory_object_stream(1)
    server_to_client_send, server_to_client_recv = anyio.create_memory_object_stream(1)

    async def run_server() -> None:
        print("Server task starting...", flush=True)
        await mcp_server.mcp._mcp_server.run(
            client_to_server_recv,
            server_to_client_send,
            mcp_server.mcp._mcp_server.create_initialization_options(),
            raise_exceptions=True,
        )
        print("Server task stopped.", flush=True)

    async with anyio.create_task_group() as tg:
        tg.start_soon(run_server)
        await anyio.sleep(0)
        async with ClientSession(
            server_to_client_recv,
            client_to_server_send,
            read_timeout_seconds=timedelta(seconds=10),
        ) as session:
            print("Session created, initializing...", flush=True)
            await session.initialize()
            print("Session initialized.", flush=True)
            tools = await session.list_tools()
            print("Tools:", [tool.name for tool in tools.tools])

            result = await session.call_tool(
                "get_reimbursement_summary",
                {"name": "张三", "month": "2025-03"},
            )
            print("Reimbursement:", result)

            ticket = await session.call_tool(
                "create_ticket",
                {
                    "title": "报销资料补充",
                    "description": "请补充 2025-03 出差住宿发票",
                    "requester": "王五",
                    "priority": "P1",
                },
            )
            print("Ticket:", ticket)
        tg.cancel_scope.cancel()


if __name__ == "__main__":
    anyio.run(main)
