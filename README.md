# Production-Ready Customer Support Agent

A comprehensive, production-grade agentic system for customer support built with Python, Claude AI, and async patterns.

## ✨ Features

### State Management
- **ConversationState**: Tracks conversation history, tool calls, metadata
- **Message History**: Full message tracking with timestamps
- **Tool Call History**: Records all tool executions with status and results
- **Session Management**: Unique session IDs for conversation tracking

### Context Management
- **Efficient Context Windows**: Smart message windowing (configurable limit)
- **Context Cache**: Caches conversation context for performance
- **Dynamic System Prompts**: Generates context-aware system prompts
- **Customer Data Integration**: Seamlessly integrates customer information

### Tool Management
- **Async Tool Execution**: Concurrent tool execution with `asyncio`
- **Automatic Retries**: Configurable retry logic with exponential backoff
- **Tool Definitions**: Automatic conversion to Claude tool definitions
- **Tool Registration**: Easy registration of custom tools

### Error Handling & Callbacks
- **Tool Success Callbacks**: Triggered on successful tool execution
- **Tool Error Callbacks**: Triggered on tool failures
- **Message Callbacks**: Triggered on message events
- **Comprehensive Logging**: File and console logging with detailed tracing

### State Persistence
- **JSON Storage**: Human-readable conversation state storage
- **File Storage**: Binary pickle-based storage for efficiency
- **Extensible**: Easy to implement database storage

## 📁 Project Structure

```
.
├── src/
│   ├── agent.py              # Core agent implementation
│   ├── state_storage.py      # State persistence layer
│   ├── main.py               # Basic usage example
│   └── example_full.py       # Full example with all features
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd AI_chat_support_assistant

# Install dependencies
pip install -r requirements.txt

# Set up environment
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Basic Usage

```python
import asyncio
from src.agent import CustomerSupportAgent

async def main():
    agent = CustomerSupportAgent(api_key="your-api-key")
    
    # Set up callbacks (optional)
    agent.set_callbacks(
        on_tool_success=lambda tc: print(f"✅ {tc.name} succeeded"),
        on_tool_error=lambda tc: print(f"❌ {tc.name} failed"),
        on_message=lambda e: print(f"📨 {e['type']}"),
    )
    
    # Process a message
    customer_data = {"id": "CUST-123", "name": "John Doe"}
    response = await agent.process_message(
        "I need help with my order",
        customer_data=customer_data
    )
    print(response)

asyncio.run(main())
```

## 🛠 Custom Tools

Create custom tools by extending the `Tool` base class:

```python
from src.agent import Tool

class MyCustomTool(Tool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="What this tool does"
        )
    
    async def execute(self, param1: str, param2: int) -> dict:
        # Tool implementation
        return {"status": "success", "result": "..."}
    
    def _get_input_schema(self) -> dict:
        return {
            "param1": {"type": "string", "description": "..."},
            "param2": {"type": "integer", "description": "..."}
        }
    
    def _get_required_fields(self) -> list:
        return ["param1", "param2"]

# Register the tool
agent.register_tool(MyCustomTool())
```

## 📊 Built-in Tools

### SearchKnowledgeBaseTool
Search the customer support knowledge base for relevant articles.

```python
# Automatically used by the agent
# Input: query (string), limit (int, optional)
```

### GetOrderStatusTool
Retrieve the status of a customer's order.

```python
# Input: order_id (string)
```

### CreateTicketTool
Create a support ticket for escalation to human team.

```python
# Input: title (string), description (string), priority (string)
```

## 💾 State Persistence

### Using JSON Storage

```python
from src.state_storage import JSONStateStorage

storage = JSONStateStorage("conversations/")

# Save state
storage.save(agent.state_manager)

# Load state
state = storage.load(session_id)
```

### Using File Storage

```python
from src.state_storage import FileStateStorage

storage = FileStateStorage("conversations/")

# Save and load like above
```

## 🔄 Callbacks & Events

Set up callbacks to react to agent events:

```python
async def on_tool_success(tool_call):
    print(f"Tool {tool_call.name} succeeded")
    print(f"Result: {tool_call.result}")

async def on_tool_error(tool_call):
    print(f"Tool {tool_call.name} failed")
    print(f"Error: {tool_call.error}")
    print(f"Retries: {tool_call.retries}/{tool_call.max_retries}")

async def on_message(event):
    print(f"Event type: {event['type']}")
    print(f"Content: {event.get('content')}")

agent.set_callbacks(
    on_tool_success=on_tool_success,
    on_tool_error=on_tool_error,
    on_message=on_message
)
```

## 📝 Examples

### Basic Example
```bash
python -m src.main
```

### Full Example with Custom Tools
```bash
python -m src.example_full
```

## 🏗 Architecture

### Agent Loop

1. **User Input** → Add to conversation state
2. **Context Building** → Build context with recent messages
3. **Claude Call** → Send to Claude with tools
4. **Tool Execution** → If Claude requests tool use:
   - Execute tools concurrently
   - Run error handling with retries
   - Trigger callbacks
5. **Response** → If Claude generates response, return it
6. **Loop** → Continue until response is generated

### State Management Flow

```
User Message
    ↓
Add to ConversationState
    ↓
Build Context (ContextManager)
    ↓
Call Claude
    ↓
Execute Tools (ToolManager)
    ↓
Update State with Results
    ↓
Generate Response
    ↓
Persist State (StateStorage)
```

## ⚙️ Configuration

### Agent Configuration

```python
agent = CustomerSupportAgent(api_key="...")

# Customize model
agent.model = "claude-3-opus-20240229"

# Customize context window
agent.context_manager = ContextManager(max_context_tokens=16000)
```

### Tool Configuration

```python
# Customize retry behavior
tool_call = ToolCall(...)
tool_call.max_retries = 5

# Customize tool execution
results = await agent.tool_manager.execute_all_tools(
    tool_calls,
    on_success=custom_success_handler,
    on_error=custom_error_handler,
)
```

## 📊 Getting Conversation State

```python
# Get full conversation state
state = agent.get_conversation_state()

# Access components
print(state['session_id'])
print(state['messages'])  # List of messages
print(state['tool_calls_history'])  # Tool execution history
print(state['context'])  # Current context
print(state['metadata'])  # Custom metadata
```

## 🐛 Logging

Enable detailed logging:

```python
from src.agent import setup_logging
import logging

# Setup logging with DEBUG level
setup_logging(level=logging.DEBUG)

# Logs are written to:
# - agent.log (file)
# - Console (stdout)
```

## 🧪 Testing

Run the examples to test the system:

```bash
# Test basic functionality
python -m src.main

# Test with custom tools and persistence
python -m src.example_full
```

## 📦 Dependencies

- `anthropic>=0.21.0` - Claude API client
- `python-dotenv>=1.0.0` - Environment variable management

## 🔐 Security

- Never commit API keys
- Use environment variables for credentials
- Store conversation data securely
- Implement access controls for state storage

## 🚢 Production Deployment

For production use:

1. **Database Storage**: Implement database backend for StateStorage
2. **API Server**: Wrap agent in FastAPI/Flask for API endpoint
3. **Rate Limiting**: Add rate limiting for API calls
4. **Monitoring**: Add prometheus metrics and alerts
5. **Load Balancing**: Use multiple agent instances behind load balancer
6. **Error Tracking**: Integrate with Sentry or similar

Example production setup:

```python
# api.py - FastAPI wrapper
from fastapi import FastAPI
from src.agent import CustomerSupportAgent

app = FastAPI()
agent = CustomerSupportAgent(api_key="...")

@app.post("/chat")
async def chat(message: str, customer_id: str):
    response = await agent.process_message(message)
    return {"response": response, "session_id": agent.state_manager.session_id}
```

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues and questions, open a GitHub issue.
