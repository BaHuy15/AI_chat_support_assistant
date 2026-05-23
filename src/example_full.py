"""Full example with state persistence, callbacks, and error handling."""

import asyncio
import os
from agent import CustomerSupportAgent, Tool, setup_logging
from state_storage import JSONStateStorage


class SendEmailTool(Tool):
    """Custom tool: Send email to customer."""

    def __init__(self):
        super().__init__(
            name="send_email",
            description="Send an email to the customer"
        )

    async def execute(self, subject: str, body: str) -> dict:
        """Send email."""
        # Simulate email sending
        import datetime
        return {
            "status": "success",
            "email_sent": True,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    def _get_input_schema(self) -> dict:
        return {
            "subject": {"type": "string", "description": "Email subject"},
            "body": {"type": "string", "description": "Email body"},
        }

    def _get_required_fields(self) -> list:
        return ["subject", "body"]


async def main():
    # Setup logging
    setup_logging()

    # Initialize storage
    storage = JSONStateStorage()

    # Initialize agent
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    agent = CustomerSupportAgent(api_key=api_key)

    # Register custom tools
    agent.register_tool(SendEmailTool())

    # Callbacks with state persistence
    async def on_tool_success(tool_call):
        print(f"✅ {tool_call.name} succeeded")
        storage.save(agent.state_manager)

    async def on_tool_error(tool_call):
        print(f"❌ {tool_call.name} failed: {tool_call.error}")
        storage.save(agent.state_manager)

    async def on_message(event):
        print(f"📨 {event['type']}: {event.get('content', '')[:50]}")
        storage.save(agent.state_manager)

    agent.set_callbacks(
        on_tool_success=on_tool_success,
        on_tool_error=on_tool_error,
        on_message=on_message,
    )

    # Simulate multi-turn conversation
    customer_data = {
        "id": "CUST-789",
        "name": "Jane Smith",
        "membership": "Premium",
    }

    messages = [
        "Hi, I have an issue with my subscription",
        "Can you help me cancel it?",
        "Please send me a confirmation email",
    ]

    for msg in messages:
        print(f"\n👤 User: {msg}")
        try:
            response = await agent.process_message(msg, customer_data)
            print(f"🤖 Agent: {response}")
        except Exception as e:
            print(f"⚠️ Error: {e}")

    # Save final state
    storage.save(agent.state_manager)
    print(f"\n✅ Conversation saved with session ID: {agent.state_manager.session_id}")


if __name__ == "__main__":
    asyncio.run(main())
