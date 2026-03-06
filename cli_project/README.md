# MCP Chat

MCP Chat is a command-line interface application that enables interactive chat capabilities with AI models through the Anthropic API or Groq API. The application supports document retrieval, command-based prompts, and extensible tool integrations via the MCP (Model Control Protocol) architecture.

## Features

- 🤖 **Dual Model Support**: Choose between Claude (Anthropic) or Groq models
- 📄 **Document Management**: Retrieve and reference documents with @mentions
- ⚡ **Command System**: Execute prompts with /commands
- 🔧 **MCP Integration**: Extensible tool system via Model Context Protocol
- 💬 **Interactive CLI**: Auto-completion and intuitive interface

## Prerequisites

- Python 3.9+
- API Key for either:
  - **Anthropic Claude** (Claude API Key), or
  - **Groq** (Groq API Key - free option)

## Setup

### Step 1: Configure the environment variables

1. Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

2. Edit `.env` and configure your chosen model provider:

**Option A: Using Groq (Free, Recommended for Learning)**
```
MODEL_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

Get your free Groq API key at: https://console.groq.com/keys

**Option B: Using Claude**
```
MODEL_PROVIDER=claude
ANTHROPIC_API_KEY=your_anthropic_api_key
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

### Step 2: Install dependencies

#### Option 1: Setup with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

1. Install uv, if not already installed:

```bash
pip install uv
```

2. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
uv pip install -e .
```

4. Run the project

```bash
uv run main.py
```

#### Option 2: Setup without uv

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install anthropic groq python-dotenv prompt-toolkit "mcp[cli]==1.8.0"
```

3. Run the project

```bash
python main.py
```

## Usage

### Basic Interaction

Simply type your message and press Enter to chat with the model.

### Document Retrieval

Use the @ symbol followed by a document ID to include document content in your query:

```
> Tell me about @deposition.md
```

### Commands

Use the / prefix to execute commands defined in the MCP server:

```
> /summarize deposition.md
```

Commands will auto-complete when you press Tab.

## MCP Architecture Flow

The application uses the Model Context Protocol (MCP) to enable tool use and resource access. Here's how the data flows during program execution:

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                  │
│  1. Initializes AI service (Claude or Groq)                      │
│  2. Creates MCPClient connections to MCP servers                 │
│  3. Creates ChatService with doc_client, clients, ai_service     │
│  4. Creates CliApp with ChatService                              │
│  5. Calls cli.initialize() and cli.run()                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        CliApp                                    │
│  - initialize(): fetches resources & prompts from ChatService    │
│  - run(): interactive prompt loop                                │
│    • Gets user input                                             │
│    • Calls ChatService.run(user_input)                           │
│    • Displays AI response                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                ChatService (extends ChatAgent)                   │
│  - _process_query(query):                                        │
│    • If /command → gets prompt from mcp_server via MCPClient     │
│    • Otherwise → extracts @mentions, retrieves doc resources     │
│      via MCPClient, builds prompt with context                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
           ┌─────────────────┴─────────────────┐
           │ MCPClient (resources & prompts)    │
           │ read_resource(), get_prompt()      │
           │        │                           │
           │        ▼                           │
           │   mcp_server.py                    │
           │   • Resources: list_docs, get_doc  │
           │   • Prompts: (defined by server)   │
           └───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       ChatAgent.run()                            │
│  - Agentic loop:                                                 │
│    1. Send messages + tools to AI service (Claude/Groq)          │
│    2. If AI response is tool_use → go to ToolManager             │
│    3. Add tool results to conversation, repeat from step 1       │
│    4. If AI response is final text → return to CliApp            │
└────────────────────────────┬────────────────────────────────────┘
                             │ (on tool_use)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ToolManager                                 │
│  - get_all_tools(): collects tools from all MCPClients           │
│  - execute_tool_requests(): finds client with matching tool,     │
│    calls tool via MCPClient, returns results to ChatAgent        │
└────────────────────────────┬────────────────────────────────────┘
                             │
           ┌─────────────────┴─────────────────┐
           │ MCPClient (tool execution)         │
           │ list_tools(), call_tool()          │
           │        │                           │
           │        ▼                           │
           │   mcp_server.py                    │
           │   • Tools: read_doc, edit_doc      │
           └───────────────────────────────────┘
```

## Development

### Adding New Documents

Edit the `mcp_server.py` file to add new documents to the `docs` dictionary.

### Implementing MCP Features

To fully implement the MCP features:

1. Complete the TODOs in `mcp_server.py`
2. Implement the missing functionality in `mcp_client.py`

### Linting and Typing Check

There are no lint or type checks implemented.

Remember: the best code is the code that works!
