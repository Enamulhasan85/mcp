from typing import Union
from ai.claude import Claude
from ai.groq_client import GroqClient
from mcp_layer.client import MCPClient
from mcp_layer.tools import ToolManager
from anthropic.types import MessageParam


class ChatAgent:
    def __init__(self, ai_service: Union[Claude, GroqClient], clients: dict[str, MCPClient]):
        self.ai_service: Union[Claude, GroqClient] = ai_service
        self.clients: dict[str, MCPClient] = clients
        self.messages: list[MessageParam] = []

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "content": query})

    async def run(self, query: str) -> str:
        await self._process_query(query)

        while True:
            response = self.ai_service.chat(
                messages=self.messages,
                tools=await ToolManager.get_all_tools(self.clients),
            )

            self.ai_service.add_assistant_message(self.messages, response)

            if response.stop_reason == "tool_use":
                print(self.ai_service.text_from_message(response))
                tool_result_parts = await ToolManager.execute_tool_requests(
                    self.clients, response
                )
                self.ai_service.add_user_message(self.messages, tool_result_parts)
            else:
                return self.ai_service.text_from_message(response)
