import asyncio
import sys
import os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_layer.client import MCPClient
from ai.claude import Claude
from ai.groq_client import GroqClient

from chat.service import ChatService
from cli.app import CliApp

load_dotenv()

# Model Selection (use "claude" or "groq")
model_provider = os.getenv("MODEL_PROVIDER", "claude").lower()

# Validate provider and get model config
if model_provider == "claude":
    claude_model = os.getenv("CLAUDE_MODEL", "")
    assert claude_model, "Error: CLAUDE_MODEL cannot be empty. Update .env"
    assert os.getenv("ANTHROPIC_API_KEY"), "Error: ANTHROPIC_API_KEY cannot be empty. Update .env"
elif model_provider == "groq":
    groq_model = os.getenv("GROQ_MODEL", "")
    assert groq_model, "Error: GROQ_MODEL cannot be empty. Update .env"
    assert os.getenv("GROQ_API_KEY"), "Error: GROQ_API_KEY cannot be empty. Update .env"
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

        chat = ChatService(
            doc_client=doc_client,
            clients=clients,
            ai_service=ai_service,
        )

        cli = CliApp(chat)
        await cli.initialize()
        await cli.run()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
