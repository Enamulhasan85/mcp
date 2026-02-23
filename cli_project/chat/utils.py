from typing import List
from mcp.types import PromptMessage
from anthropic.types import MessageParam


def convert_prompt_message_to_message_param(
    prompt_message: PromptMessage,
) -> MessageParam:
    """Convert MCP PromptMessage to Anthropic MessageParam format."""
    role = "user" if prompt_message.role == "user" else "assistant"
    content = prompt_message.content

    # Extract text from content (handles both dict and object formats)
    def get_text(obj):
        if isinstance(obj, dict):
            return obj.get("text", "")
        return getattr(obj, "text", "")
    
    def get_type(obj):
        if isinstance(obj, dict):
            return obj.get("type", None)
        return getattr(obj, "type", None)

    # Single text content
    if get_type(content) == "text":
        return {"role": role, "content": get_text(content)}

    # Multiple content blocks (list)
    if isinstance(content, list):
        text_blocks = [
            {"type": "text", "text": get_text(item)}
            for item in content
            if get_type(item) == "text"
        ]
        if text_blocks:
            return {"role": role, "content": text_blocks}

    return {"role": role, "content": ""}


def convert_prompt_messages_to_message_params(
    prompt_messages: List[PromptMessage],
) -> List[MessageParam]:
    return [
        convert_prompt_message_to_message_param(msg) for msg in prompt_messages
    ]
