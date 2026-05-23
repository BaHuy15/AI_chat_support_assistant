"""Production-ready customer support agent with state management."""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

import anthropic


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

class MessageRole(str, Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ToolStatus(str, Enum):
    """Tool execution status."""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRIED = "retried"


@dataclass
class ToolCall:
    """Represents a single tool call."""
    id: str
    name: str
    input: Dict[str, Any]
    status: ToolStatus = ToolStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Message:
    """Represents a message in conversation."""
    role: MessageRole
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tool_calls: List[ToolCall] = field(default_factory=list)


@dataclass
class ConversationState:
    """Manages conversation state."""
    session_id: str
    messages: List[Message] = field(default_factory=list)
    tool_calls_history: Dict[str, ToolCall] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_message(self, role: MessageRole, content: str, tool_calls: Optional[List[ToolCall]] = None) -> Message:
        """Add message to conversation state."""
        msg = Message(role=role, content=content, tool_calls=tool_calls or [])
        self.messages.append(msg)
        self.updated_at = datetime.utcnow().isoformat()
        return msg

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages for context."""
        recent = self.messages[-limit:]
        return [
            {
                "role": msg.role.value,
                "content": msg.content
            }
            for msg in recent
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary."""
        return asdict(self)


# ============================================================================
# CONTEXT MANAGEMENT
# ============================================================================

class ContextManager:
    """Manages conversation context with efficient retrieval."""

    def __init__(self, max_context_tokens: int = 8000):
        self.max_context_tokens = max_context_tokens
        self.context_cache: Dict[str, Any] = {}

    def build_context(self, state: ConversationState, customer_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build comprehensive context for agent."""
        context = {
            "session_id": state.session_id,
            "customer": customer_data or {},
            "recent_messages": state.get_recent_messages(limit=5),
            "conversation_summary": self._generate_summary(state),
            "metadata": state.metadata,
        }
        self.context_cache[state.session_id] = context
        return context

    def _generate_summary(self, state: ConversationState) -> str:
        """Generate conversation summary."""
        if len(state.messages) < 2:
            return ""

        # Simple summary: last user message + intent
        user_messages = [msg for msg in state.messages if msg.role == MessageRole.USER]
        if user_messages:
            return f"Last inquiry: {user_messages[-1].content[:100]}"
        return ""

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """Generate system prompt with context."""
        customer_info = context.get("customer", {})
        customer_str = f"\nCustomer: {customer_info}" if customer_info else ""

        return f"""You are a professional customer support agent. Your role is to:
1. Help customers with their issues
2. Use available tools to resolve problems
3. Provide clear, empathetic responses
4. Escalate complex issues when needed

{customer_str}

Guidelines:
- Be concise and helpful
- Ask clarifying questions when needed
- Use tools appropriately
- Never make promises you can't keep"""


# ============================================================================
# TOOL MANAGEMENT
# ============================================================================

class Tool(ABC):
    """Base class for agent tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool."""
        pass

    def to_definition(self) -> Dict[str, Any]:
        """Convert to Claude tool definition."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self._get_input_schema(),
                "required": self._get_required_fields(),
            }
        }

    @abstractmethod
    def _get_input_schema(self) -> Dict[str, Any]:
        """Define input schema."""
        pass

    @abstractmethod
    def _get_required_fields(self) -> List[str]:
        """Define required fields."""
        pass


class SearchKnowledgeBaseTool(Tool):
    """Search knowledge base for solutions."""

    def __init__(self):
        super().__init__(
            name="search_knowledge_base",
            description="Search the customer support knowledge base for relevant articles and solutions"
        )

    async def execute(self, query: str, limit: int = 3) -> Dict[str, Any]:
        """Search knowledge base."""
        # Simulate knowledge base search
        results = [
            {
                "title": f"Article about {query}",
                "content": f"Information regarding {query}...",
                "relevance_score": 0.95
            }
        ]
        return {
            "status": "success",
            "results": results[:limit]
        }

    def _get_input_schema(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return"
            }
        }

    def _get_required_fields(self) -> List[str]:
        return ["query"]


class GetOrderStatusTool(Tool):
    """Get customer order status."""

    def __init__(self):
        super().__init__(
            name="get_order_status",
            description="Retrieve the status of a customer's order"
        )

    async def execute(self, order_id: str) -> Dict[str, Any]:
        """Get order status."""
        # Simulate order lookup
        return {
            "status": "success",
            "order_id": order_id,
            "order_status": "shipped",
            "tracking_number": "123456789",
            "estimated_delivery": "2026-05-28"
        }

    def _get_input_schema(self) -> Dict[str, Any]:
        return {
            "order_id": {
                "type": "string",
                "description": "Order ID"
            }
        }

    def _get_required_fields(self) -> List[str]:
        return ["order_id"]


class CreateTicketTool(Tool):
    """Create support ticket for escalation."""

    def __init__(self):
        super().__init__(
            name="create_ticket",
            description="Create a support ticket for escalation to human team"
        )

    async def execute(self, title: str, description: str, priority: str = "medium") -> Dict[str, Any]:
        """Create support ticket."""
        ticket_id = f"TKT-{uuid4().hex[:8].upper()}"
        return {
            "status": "success",
            "ticket_id": ticket_id,
            "title": title,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat()
        }

    def _get_input_schema(self) -> Dict[str, Any]:
        return {
            "title": {
                "type": "string",
                "description": "Ticket title"
            },
            "description": {
                "type": "string",
                "description": "Issue description"
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"],
                "description": "Priority level"
            }
        }

    def _get_required_fields(self) -> List[str]:
        return ["title", "description"]


class ToolManager:
    """Manages tool execution with error handling and retries."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
        self.on_success: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

    def register_tool(self, tool: Tool) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool
        self.logger.info(f"Tool registered: {tool.name}")

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions for Claude."""
        return [tool.to_definition() for tool in self.tools.values()]

    async def execute_tool(
        self,
        tool_call: ToolCall,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> ToolCall:
        """Execute tool with error handling and callbacks."""
        tool_call.status = ToolStatus.EXECUTING
        self.logger.info(f"Executing tool: {tool_call.name} (ID: {tool_call.id})")

        try:
            if tool_call.name not in self.tools:
                raise ValueError(f"Tool not found: {tool_call.name}")

            tool = self.tools[tool_call.name]
            result = await tool.execute(**tool_call.input)

            tool_call.result = result
            tool_call.status = ToolStatus.SUCCESS
            self.logger.info(f"Tool executed successfully: {tool_call.name}")

            # Success callback
            if on_success:
                await on_success(tool_call)
            if self.on_success:
                await self.on_success(tool_call)

            return tool_call

        except Exception as e:
            self.logger.error(f"Tool execution failed: {str(e)}", exc_info=True)
            tool_call.error = str(e)

            # Retry logic
            if tool_call.retries < tool_call.max_retries:
                tool_call.retries += 1
                tool_call.status = ToolStatus.RETRIED
                self.logger.info(f"Retrying tool: {tool_call.name} (attempt {tool_call.retries})")
                await asyncio.sleep(1)  # Exponential backoff could be added
                return await self.execute_tool(tool_call, on_success, on_error)

            tool_call.status = ToolStatus.FAILED

            # Error callback
            if on_error:
                await on_error(tool_call)
            if self.on_error:
                await self.on_error(tool_call)

            return tool_call

    async def execute_all_tools(
        self,
        tool_calls: List[ToolCall],
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> List[ToolCall]:
        """Execute multiple tools concurrently."""
        tasks = [
            self.execute_tool(tc, on_success, on_error)
            for tc in tool_calls
        ]
        return await asyncio.gather(*tasks)


# ============================================================================
# AGENT
# ============================================================================

class CustomerSupportAgent:
    """Production-ready customer support agent."""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.state_manager = ConversationState(session_id=str(uuid4()))
        self.context_manager = ContextManager()
        self.tool_manager = ToolManager()
        self.logger = logging.getLogger(__name__)

        # Register tools
        self._register_default_tools()

        # Callbacks
        self.on_tool_success: Optional[Callable] = None
        self.on_tool_error: Optional[Callable] = None
        self.on_message: Optional[Callable] = None

    def _register_default_tools(self) -> None:
        """Register default tools."""
        self.tool_manager.register_tool(SearchKnowledgeBaseTool())
        self.tool_manager.register_tool(GetOrderStatusTool())
        self.tool_manager.register_tool(CreateTicketTool())

    def register_tool(self, tool: Tool) -> None:
        """Register a custom tool."""
        self.tool_manager.register_tool(tool)

    async def process_message(
        self,
        user_message: str,
        customer_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Process user message and generate response."""
        self.logger.info(f"Processing message: {user_message[:50]}...")

        # Add user message to state
        self.state_manager.add_message(MessageRole.USER, user_message)

        # Build context
        context = self.context_manager.build_context(self.state_manager, customer_data)
        system_prompt = self.context_manager.get_system_prompt(context)

        # Agentic loop
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            self.logger.debug(f"Agent iteration: {iteration}")

            # Call Claude with tools
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                tools=self.tool_manager.get_tool_definitions(),
                messages=self.state_manager.get_recent_messages(),
            )

            # Parse response
            if response.stop_reason == "tool_use":
                # Extract tool calls
                tool_calls = []
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_call = ToolCall(
                            id=content_block.id,
                            name=content_block.name,
                            input=content_block.input,
                        )
                        tool_calls.append(tool_call)

                # Execute tools
                results = await self.tool_manager.execute_all_tools(
                    tool_calls,
                    on_success=self.on_tool_success,
                    on_error=self.on_tool_error,
                )

                # Add assistant message with tool calls
                assistant_message = ""
                for content_block in response.content:
                    if hasattr(content_block, "text"):
                        assistant_message = content_block.text
                        break

                self.state_manager.add_message(
                    MessageRole.ASSISTANT,
                    assistant_message or "Processing...",
                    tool_calls=results,
                )

                # Add tool results to messages
                tool_results_content = []
                for result in results:
                    tool_results_content.append({
                        "type": "tool_result",
                        "tool_use_id": result.id,
                        "content": str(result.result or result.error),
                    })

                # Continue loop with tool results
                messages = self.state_manager.get_recent_messages()
                messages.append({
                    "role": "user",
                    "content": tool_results_content,
                })
                self.state_manager.messages[-1].content += f"\n[Tool results: {len(results)} executed]"

            elif response.stop_reason == "end_turn":
                # Final response
                final_response = ""
                for content_block in response.content:
                    if hasattr(content_block, "text"):
                        final_response = content_block.text
                        break

                # Add final response to state
                self.state_manager.add_message(MessageRole.ASSISTANT, final_response)

                # Callback
                if self.on_message:
                    await self.on_message({
                        "type": "response",
                        "content": final_response,
                        "session_id": self.state_manager.session_id,
                    })

                self.logger.info(f"Response generated: {final_response[:50]}...")
                return final_response

            else:
                self.logger.warning(f"Unexpected stop reason: {response.stop_reason}")
                break

        raise RuntimeError("Agent failed to generate response within max iterations")

    def get_conversation_state(self) -> Dict[str, Any]:
        """Get current conversation state."""
        return self.state_manager.to_dict()

    def set_callbacks(
        self,
        on_tool_success: Optional[Callable] = None,
        on_tool_error: Optional[Callable] = None,
        on_message: Optional[Callable] = None,
    ) -> None:
        """Set callbacks for agent events."""
        self.on_tool_success = on_tool_success
        self.on_tool_error = on_tool_error
        self.on_message = on_message
        self.tool_manager.on_success = on_tool_success
        self.tool_manager.on_error = on_tool_error


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(level: int = logging.INFO) -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('agent.log'),
            logging.StreamHandler(),
        ]
    )
