import asyncio
import sys
import os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_client import MCPClient
from core.claude import Claude
from core.groq_client import GroqClient

from core.cli_chat import CliChat
from core.cli import CliApp

load_dotenv()

# Model Selection (use "claude" or "groq")
model_provider = os.getenv("MODEL_PROVIDER", "claude").lower()

# Anthropic Config
claude_model = os.getenv("CLAUDE_MODEL", "")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

# Groq Config
groq_model = os.getenv("GROQ_MODEL", "")
groq_api_key = os.getenv("GROQ_API_KEY", "")

# Validate based on selected provider
if model_provider == "claude":
    assert claude_model, "Error: CLAUDE_MODEL cannot be empty. Update .env"
    assert anthropic_api_key, "Error: ANTHROPIC_API_KEY cannot be empty. Update .env"
elif model_provider == "groq":
    assert groq_model, "Error: GROQ_MODEL cannot be empty. Update .env"
    assert groq_api_key, "Error: GROQ_API_KEY cannot be empty. Update .env"
else:
    raise ValueError(f"Invalid MODEL_PROVIDER: {model_provider}. Use 'claude' or 'groq'")


async def main():
    # Initialize the appropriate AI service
    if model_provider == "claude":
        ai_service = Claude(model=claude_model)
        print(f"Using Claude model: {claude_model}")
    else:  # groq
        ai_service = GroqClient(model=groq_model)
        print(f"Using Groq model: {groq_model}")

    server_scripts = sys.argv[1:]
    clients = {}

    command, args = (
        ("uv", ["run", "mcp_server.py"])
        if os.getenv("USE_UV", "0") == "1"
        else ("python", ["mcp_server.py"])
    )

    async with AsyncExitStack() as stack:
        doc_client = await stack.enter_async_context(
            MCPClient(command=command, args=args)
        )
        clients["doc_client"] = doc_client

        for i, server_script in enumerate(server_scripts):
            client_id = f"client_{i}_{server_script}"
            client = await stack.enter_async_context(
                MCPClient(command="uv", args=["run", server_script])
            )
            clients[client_id] = client

        chat = CliChat(
            doc_client=doc_client,
            clients=clients,
            claude_service=ai_service,  # Works for both Claude and Groq
        )

        cli = CliApp(chat)
        await cli.initialize()
        await cli.run()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
