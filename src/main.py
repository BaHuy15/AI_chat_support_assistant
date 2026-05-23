"""Example usage of the production-ready agent."""

import asyncio
import os
from agent import CustomerSupportAgent, setup_logging


async def on_tool_success(tool_call):
    """Callback when tool succeeds."""
    print(f"✅ Tool {tool_call.name} succeeded: {tool_call.result}")


async def on_tool_error(tool_call):
    """Callback when tool fails."""
    print(f"❌ Tool {tool_call.name} failed: {tool_call.error}")
    print(f"   Retries: {tool_call.retries}/{tool_call.max_retries}")


async def on_message(event):
    """Callback when message is processed."""
    print(f"\n📨 Message event: {event['type']}")


async def main():
    # Setup logging
    setup_logging()

    # Initialize agent
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    agent = CustomerSupportAgent(api_key=api_key)

    # Set callbacks
    agent.set_callbacks(
        on_tool_success=on_tool_success,
        on_tool_error=on_tool_error,
        on_message=on_message,
    )

    # Simulate customer data
    customer_data = {
        "id": "CUST-12345",
        "name": "John Doe",
        "email": "john@example.com",
        "account_status": "active",
    }

    # Multi-turn conversation
    conversations = [
        "Hi, I need help with my order",
        "My order number is ORD-99999",
        "When will it arrive?",
    ]

    for user_input in conversations:
        print(f"\n👤 User: {user_input}")
        try:
            response = await agent.process_message(user_input, customer_data)
            print(f"🤖 Agent: {response}")
        except Exception as e:
            print(f"⚠️ Error: {e}")

    # Get final state
    state = agent.get_conversation_state()
    print(f"\n📊 Conversation State:")
    print(f"  Session ID: {state['session_id']}")
    print(f"  Messages: {len(state['messages'])}")
    print(f"  Total tool calls: {len(state['tool_calls_history'])}")


if __name__ == "__main__":
    asyncio.run(main())
