from groq import Groq
import json


class GroqClient:
    def __init__(self, model: str):
        self.client = Groq()
        self.model = model

    def add_user_message(self, messages: list, message):
        """Add user message to conversation history."""
        if isinstance(message, list):
            # Handle tool results
            content = []
            for item in message:
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    # Convert tool result to Groq format
                    content.append({
                        "type": "text",
                        "text": json.dumps({
                            "tool_call_id": item.get("tool_use_id"),
                            "result": item.get("content")
                        })
                    })
            user_message = {
                "role": "user",
                "content": json.dumps([c["text"] for c in content]) if content else "Tool execution completed"
            }
        else:
            user_message = {
                "role": "user",
                "content": message.get("content") if isinstance(message, dict) else message,
            }
        messages.append(user_message)

    def add_assistant_message(self, messages: list, message):
        """Add assistant message to conversation history."""
        if hasattr(message, "choices"):
            # Groq response format
            choice = message.choices[0]
            content = choice.message.content or ""
            
            assistant_message = {
                "role": "assistant",
                "content": content,
            }
            
            # Add tool calls if present
            if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in choice.message.tool_calls
                ]
        else:
            assistant_message = {
                "role": "assistant",
                "content": message if isinstance(message, str) else str(message),
            }
        messages.append(assistant_message)

    def text_from_message(self, message):
        """Extract text content from Groq response."""
        if hasattr(message, "choices") and len(message.choices) > 0:
            return message.choices[0].message.content or ""
        return ""

    def chat(
        self,
        messages,
        system=None,
        temperature=1.0,
        stop_sequences=[],
        tools=None,
        thinking=False,
        thinking_budget=1024,
    ):
        """
        Chat with Groq model.
        Note: Groq doesn't support extended thinking like Claude.
        """
        # Prepare messages with system message if provided
        chat_messages = messages.copy()
        if system:
            chat_messages = [{"role": "system", "content": system}] + chat_messages

        params = {
            "model": self.model,
            "messages": chat_messages,
            "temperature": temperature,
        }

        # Add stop sequences if provided
        if stop_sequences:
            params["stop"] = stop_sequences

        # Add tools if provided
        if tools:
            # Convert Claude tool format to Groq/OpenAI format
            groq_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["input_schema"],
                    },
                }
                for tool in tools
            ]
            params["tools"] = groq_tools

        response = self.client.chat.completions.create(**params)
        
        # Add a stop_reason attribute for compatibility with Claude response format
        if hasattr(response.choices[0], "finish_reason"):
            if response.choices[0].finish_reason == "tool_calls":
                response.stop_reason = "tool_use"
            else:
                response.stop_reason = response.choices[0].finish_reason
        
        # Add content attribute for compatibility
        if hasattr(response.choices[0].message, "tool_calls") and response.choices[0].message.tool_calls:
            # Convert tool calls to Claude-like format
            response.content = []
            if response.choices[0].message.content:
                response.content.append(type('obj', (object,), {
                    'type': 'text',
                    'text': response.choices[0].message.content
                })())
            
            for tc in response.choices[0].message.tool_calls:
                response.content.append(type('obj', (object,), {
                    'type': 'tool_use',
                    'id': tc.id,
                    'name': tc.function.name,
                    'input': json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                })())
        else:
            response.content = [type('obj', (object,), {
                'type': 'text',
                'text': response.choices[0].message.content or ""
            })()]
        
        return response
