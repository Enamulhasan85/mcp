# Architecture Guide

## Current Structure

```
cli_project/
├── main.py               # Entry point & wiring
├── mcp_client.py         # MCP protocol client
├── mcp_server.py         # MCP document server
├── core/
│   ├── chat.py           # Base chat loop (agent loop)
│   ├── cli_chat.py       # CLI-specific chat (resource/command handling)
│   ├── cli.py            # UI layer (prompt_toolkit shell)
│   ├── claude.py         # Anthropic adapter
│   ├── groq_client.py    # Groq adapter
│   └── tools.py          # Tool execution manager
```

## Problems with the Current Structure

| Problem | Where |
|---|---|
| `core/` is a flat dumping ground — UI, business logic, and infrastructure all sit at the same level | `core/` |
| `mcp_client.py` sits at the root alongside `main.py` instead of being grouped with MCP code | root |
| `cli.py` mixes UI components (completers, key bindings) with the main app class | `core/cli.py` |
| Utility free-functions (`convert_prompt_messages_to_message_params`) live inside `cli_chat.py` | `core/cli_chat.py` |

---

## Recommended Structure

```
cli_project/
├── main.py                         # Entry point & wiring
├── mcp_server.py                   # Standalone MCP server (separate process)
│
├── ai/                             # AI provider clients
│   ├── __init__.py
│   ├── claude.py                   # Anthropic client
│   └── groq_client.py             # Groq client
│
├── mcp_layer/                      # MCP protocol layer
│   ├── __init__.py
│   ├── client.py                   # MCPClient (moved from root)
│   └── tools.py                    # Tool discovery & execution
│
├── chat/                           # Chat logic
│   ├── __init__.py
│   ├── agent.py                    # Core agent loop (call AI → handle tools → repeat)
│   ├── service.py                  # Higher-level: resolve @mentions, /commands, build prompts
│   └── utils.py                    # Helpers (prompt message converters)
│
└── cli/                            # UI layer (prompt_toolkit)
    ├── __init__.py
    ├── app.py                      # CliApp (main shell loop)
    └── completers.py               # UnifiedCompleter, CommandAutoSuggest
```

---

## What Each Folder Does

| Folder | Responsibility |
|---|---|
| `ai/` | Talks to AI APIs (Anthropic, Groq). Each file is a self-contained client. |
| `mcp_layer/` | Talks to MCP servers. Client connection + tool execution. |
| `chat/` | Business logic. The agent loop, query processing, document resolution. |
| `cli/` | User-facing terminal UI. prompt_toolkit setup, completers, key bindings. |

---

## File Mapping: Current → Target

| Current | Target |
|---|---|
| `core/claude.py` | `ai/claude.py` |
| `core/groq_client.py` | `ai/groq_client.py` |
| `mcp_client.py` | `mcp_layer/client.py` |
| `core/tools.py` | `mcp_layer/tools.py` |
| `core/chat.py` | `chat/agent.py` |
| `core/cli_chat.py` | `chat/service.py` + `chat/utils.py` |
| `core/cli.py` | `cli/app.py` + `cli/completers.py` |
| `mcp_server.py` | `mcp_server.py` (stays at root, separate process) |
| `main.py` | `main.py` (stays at root, gets cleaner imports) |

---

## What `main.py` Should Look Like After Refactor

```python
import asyncio, sys, os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from ai.claude import Claude
from ai.groq_client import GroqClient
from mcp_layer.client import MCPClient
from chat.service import ChatService
from cli.app import CliApp

load_dotenv()

model_provider = os.getenv("MODEL_PROVIDER", "claude").lower()

async def main():
    if model_provider == "claude":
        ai_service = Claude(model=os.getenv("CLAUDE_MODEL"))
    else:
        ai_service = GroqClient(model=os.getenv("GROQ_MODEL"))

    command, args = (
        ("uv", ["run", "mcp_server.py"])
        if os.getenv("USE_UV", "0") == "1"
        else ("python", ["mcp_server.py"])
    )

    async with AsyncExitStack() as stack:
        doc_client = await stack.enter_async_context(
            MCPClient(command=command, args=args)
        )

        chat = ChatService(
            doc_client=doc_client,
            clients={"doc_client": doc_client},
            ai_service=ai_service,
        )

        app = CliApp(chat)
        await app.initialize()
        await app.run()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
```

---

## Splitting `cli.py` into `cli/app.py` + `cli/completers.py`

Move `CommandAutoSuggest` and `UnifiedCompleter` into `cli/completers.py`. Keep `CliApp` in `cli/app.py`. This keeps each file focused on one thing.

## Splitting `cli_chat.py` into `chat/service.py` + `chat/utils.py`

Move `convert_prompt_message_to_message_param` and `convert_prompt_messages_to_message_params` into `chat/utils.py`. Keep `CliChat` (renamed to `ChatService`) in `chat/service.py`.
