"""
LangChain Tool Call Examples with Agent Breadcrumbs

This file demonstrates various LangChain agent scenarios to show how
agent-breadcrumbs captures LLM decision-making, tool usage, and costs.

Perfect for beginners who want to understand what their AI agents are doing!
"""

import os
from agent_breadcrumbs.integrations.langchain import enable_breadcrumbs
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


@tool
def add(a: int, b: int) -> int:
    """Add two integers together."""
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers together."""
    return a * b


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # Mock weather data for demo
    weather_data = {
        "San Francisco": "Sunny, 72°F",
        "New York": "Cloudy, 65°F",
        "London": "Rainy, 55°F",
        "Tokyo": "Clear, 78°F",
    }
    return weather_data.get(city, f"Weather data not available for {city}")


@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # Mock search results for demo
    results = {
        "python": "Python is a high-level programming language...",
        "ai": "Artificial Intelligence (AI) refers to computer systems...",
        "weather": "Weather is the state of the atmosphere...",
        "news": "Latest news includes developments in technology...",
    }
    for key in results:
        if key.lower() in query.lower():
            return results[key]
    return f"Search results for '{query}': Multiple relevant articles found."


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert currency amounts."""
    # Mock exchange rates for demo
    rates = {
        ("USD", "EUR"): 0.85,
        ("EUR", "USD"): 1.18,
        ("USD", "GBP"): 0.73,
        ("GBP", "USD"): 1.37,
    }

    rate = rates.get((from_currency.upper(), to_currency.upper()), 1.0)
    converted = amount * rate
    return f"{amount} {from_currency.upper()} = {converted:.2f} {to_currency.upper()}"


# ============================================================================
# HELPER FUNCTION
# ============================================================================


def create_agent(tools, system_message="You are a helpful assistant."):
    """Helper to create an agent with observability"""
    callback = enable_breadcrumbs()

    model = init_chat_model(
        "gpt-4o-mini", model_provider="openai", callbacks=[callback]
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    agent = create_tool_calling_agent(model, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, tools=tools, callbacks=[callback], verbose=True
    )

    return agent_executor, callback


def print_session_summary(callback, title):
    """Print a nice summary of what happened"""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}")

    history = callback.logger.get_session_history()

    step = 1
    for action in history:
        if action.action_type == "llm_call":
            import json

            output_data = json.loads(action.output_data)

            print(f"\n🤖 LLM Decision #{step}")
            print(f"   Model: {action.model_name}")
            print(
                f"   Tokens: {action.token_usage.prompt_tokens if action.token_usage else 'N/A'}→{action.token_usage.completion_tokens if action.token_usage else 'N/A'}"
            )
            print(
                f"   Cost: ${action.cost_usd:.6f}"
                if action.cost_usd
                else "   Cost: N/A"
            )
            print(
                f"   Duration: {action.duration_ms:.1f}ms"
                if action.duration_ms
                else "   Duration: N/A"
            )

            response = output_data.get("response", "")
            print(f"   🎯 Decision: {response}")
            step += 1

        elif action.action_type == "tool_use":
            import json

            input_data = json.loads(action.input_data)
            output_data = json.loads(action.output_data)

            print(f"\n🔧 Tool Execution")
            print(f"   Tool: {input_data.get('tool', 'unknown')}")
            print(f"   Input: {input_data.get('input', {})}")
            print(f"   Result: {output_data.get('result', 'N/A')}")

    # Show cost summary
    cost_summary = callback.logger.get_session_cost_summary()
    print(f"\n💰 Session Summary")
    print(f"   Total Cost: ${cost_summary['total_cost_usd']:.6f}")
    print(f"   Total Tokens: {cost_summary['total_tokens']}")
    print(
        f"   LLM Decisions: {len([a for a in history if a.action_type == 'llm_call'])}"
    )
    print(f"   Tool Uses: {len([a for a in history if a.action_type == 'tool_use'])}")


# ============================================================================
# EXAMPLE 1: SIMPLE MATH CALCULATION
# ============================================================================


def example_simple_math():
    """Simple math with one tool call"""
    print("\n🧮 EXAMPLE 1: Simple Math Calculation")
    print("Shows: Single tool decision, cost tracking")

    tools = [add]
    agent, callback = create_agent(
        tools, "You are a calculator. Use the add tool for addition problems."
    )

    result = agent.invoke({"input": "What is 25 + 17?"})
    print(f"\n✅ Final Answer: {result['output']}")

    print_session_summary(callback, "Simple Math Example")


# ============================================================================
# EXAMPLE 2: MULTI-STEP MATH
# ============================================================================


def example_multi_step_math():
    """Complex math requiring multiple tool calls"""
    print("\n🔢 EXAMPLE 2: Multi-Step Math Calculation")
    print("Shows: Multiple tool decisions, sequential reasoning")

    tools = [add, multiply]
    agent, callback = create_agent(
        tools, "You are a math assistant. Use tools to solve problems step by step."
    )

    result = agent.invoke({"input": "What is (15 + 25) * 3?"})
    print(f"\n✅ Final Answer: {result['output']}")

    print_session_summary(callback, "Multi-Step Math Example")


# ============================================================================
# EXAMPLE 3: INFORMATION RETRIEVAL
# ============================================================================


def example_weather_lookup():
    """Weather information retrieval"""
    print("\n🌤️  EXAMPLE 3: Weather Information Lookup")
    print("Shows: Information retrieval, decision making")

    tools = [get_weather]
    agent, callback = create_agent(
        tools,
        "You are a weather assistant. Use the get_weather tool to provide current weather information.",
    )

    result = agent.invoke({"input": "What's the weather like in San Francisco?"})
    print(f"\n✅ Final Answer: {result['output']}")

    print_session_summary(callback, "Weather Lookup Example")


# ============================================================================
# EXAMPLE 4: MULTI-TOOL INFORMATION GATHERING
# ============================================================================


def example_travel_planning():
    """Travel planning with multiple information sources"""
    print("\n✈️  EXAMPLE 4: Travel Planning Assistant")
    print("Shows: Multiple tool types, information synthesis")

    tools = [get_weather, convert_currency, search_web]
    agent, callback = create_agent(
        tools,
        "You are a travel planning assistant. Help users plan trips by checking weather, currency rates, and finding relevant information.",
    )

    result = agent.invoke(
        {
            "input": "I'm planning a trip to London. Can you check the weather and convert $500 to British pounds?"
        }
    )
    print(f"\n✅ Final Answer: {result['output']}")

    print_session_summary(callback, "Travel Planning Example")


# ============================================================================
# EXAMPLE 5: NO TOOLS NEEDED
# ============================================================================


def example_no_tools():
    """Example where LLM answers without tools"""
    print("\n💭 EXAMPLE 5: No Tools Needed")
    print("Shows: LLM reasoning without tool usage")

    tools = [add, multiply, get_weather]  # Tools available but not needed
    agent, callback = create_agent(
        tools, "You are a helpful assistant. Only use tools when specifically needed."
    )

    result = agent.invoke({"input": "What is the capital of France?"})
    print(f"\n✅ Final Answer: {result['output']}")

    print_session_summary(callback, "No Tools Needed Example")


# ============================================================================
# EXAMPLE 6: ERROR HANDLING
# ============================================================================


def example_tool_selection():
    """Shows how LLM chooses between multiple tools"""
    print("\n🤔 EXAMPLE 6: Tool Selection Reasoning")
    print("Shows: LLM choosing appropriate tools from multiple options")

    tools = [add, multiply, get_weather, search_web, convert_currency]
    agent, callback = create_agent(
        tools,
        "You are a helpful assistant with access to various tools. Choose the most appropriate tool for each request.",
    )

    result = agent.invoke(
        {
            "input": "I need to calculate the total cost: 3 items at $15 each, plus 2 items at $8 each."
        }
    )
    print(f"\n✅ Final Answer: {result['output']}")

    print_session_summary(callback, "Tool Selection Example")


# ============================================================================
# EXAMPLE 7: COST COMPARISON
# ============================================================================


def example_cost_comparison():
    """Compare costs between different models"""
    print("\n💰 EXAMPLE 7: Cost Comparison Between Models")
    print("Shows: Different model costs for same task")

    tools = [add, multiply]

    # Test with gpt-4o-mini
    print("\n--- Using GPT-4o-mini ---")
    agent_mini, callback_mini = create_agent(tools, "You are a math assistant.")
    result_mini = agent_mini.invoke({"input": "Calculate (12 + 8) * 5"})

    cost_mini = callback_mini.logger.get_session_cost_summary()["total_cost_usd"]
    tokens_mini = callback_mini.logger.get_session_cost_summary()["total_tokens"]

    print(f"Result: {result_mini['output']}")
    print(f"Cost: ${cost_mini:.6f}")
    print(f"Tokens: {tokens_mini}")

    # Note: You could test other models here if available
    print("\n💡 Tip: Try different models to see cost differences!")
    print("    - gpt-4o-mini: Cheaper, good for simple tasks")
    print("    - gpt-4o: More expensive, better for complex reasoning")


# ============================================================================
# MAIN FUNCTION TO RUN ALL EXAMPLES
# ============================================================================


def run_all_examples():
    """Run all examples to demonstrate different agent scenarios"""
    print("🚀 Agent Breadcrumbs - LangChain Examples")
    print("=" * 60)
    print("These examples show how to use agent-breadcrumbs to understand")
    print("what your AI agents are thinking and how much they cost!")

    examples = [
        example_simple_math,
        example_multi_step_math,
        example_weather_lookup,
        example_travel_planning,
        example_no_tools,
        example_tool_selection,
        example_cost_comparison,
    ]

    for i, example in enumerate(examples, 1):
        try:
            example()
            if i < len(examples):
                input(f"\n⏸️  Press Enter to continue to example {i + 1}...")
        except Exception as e:
            print(f"\n❌ Error in example {i}: {e}")
            print("Continuing to next example...")

    print("\n🎉 All examples completed!")
    print("\n💡 Key Takeaways:")
    print("   • See exactly what tools your LLM decides to use")
    print("   • Track token usage and costs for each decision")
    print("   • Understand the sequence of LLM reasoning")
    print("   • Compare performance across different models")
    print("\n📊 Check your CSV file for detailed logs!")


if __name__ == "__main__":
    # You can run individual examples or all of them

    # Run single example:
    # example_simple_math()

    # Run all examples:
    run_all_examples()
