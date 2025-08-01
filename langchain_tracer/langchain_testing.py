"""
Enhanced LangChain Tool Calling Test with Complete Flow Capture

This test will capture:
1. Initial user query
2. LLM tool call decision
3. Tool execution results
4. Final LLM response after processing tool results

Run this to test the enhanced HTTP tracer!
"""

import os
import sys
import time
from datetime import datetime

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Add the langchain_tracer to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "langchain_tracer"))


def test_enhanced_http_tracer():
    """Test the enhanced HTTP tracer with complete tool flow capture"""
    try:
        from langchain_tracer import enable_http_tracing, get_http_tracer
        from langchain_tracer.models.config import TracerConfig

        print("🔍 Setting up Enhanced Agent Breadcrumbs HTTP Tracer...")

        # Configure enhanced tracing
        config = TracerConfig(
            output_file="enhanced_langchain_traces.csv",
            session_id="enhanced_test_session",
            dashboard_enabled=True,
            dashboard_port=8080,
            include_metadata=True,
            capture_tool_calls=True,
            capture_tool_responses=True,
        )

        tracer = enable_http_tracing(config)
        print("✅ Enhanced HTTP Tracer enabled!")
        print(f"   📁 Output: {config.output_file}")
        print(f"   🆔 Session: {config.session_id}")
        print(f"   📊 Dashboard: http://localhost:{config.dashboard_port}")

        return tracer

    except ImportError as e:
        print(f"❌ Failed to import langchain_tracer: {e}")
        return None
    except Exception as e:
        print(f"❌ Error setting up enhanced tracer: {e}")
        return None


def create_enhanced_test_tools():
    """Create tools with better output for testing"""
    from langchain_core.tools import tool

    @tool
    def calculator(expression: str) -> str:
        """Safely evaluate mathematical expressions with detailed output."""
        try:
            # Simple math evaluation
            result = eval(expression.replace("^", "**").replace("x", "*"))
            return f"Math calculation: {expression} = {result}"
        except Exception as e:
            return f"Math Error: Could not calculate '{expression}' - {str(e)}"

    @tool
    def weather_checker(city: str, units: str = "celsius") -> str:
        """Get current weather for a city with detailed response."""
        # Mock weather data for testing
        weather_data = {
            "San Francisco": {"temp": 22, "condition": "Sunny", "humidity": 65},
            "New York": {"temp": 18, "condition": "Cloudy", "humidity": 70},
            "London": {"temp": 12, "condition": "Rainy", "humidity": 85},
            "Tokyo": {"temp": 25, "condition": "Clear", "humidity": 60},
        }

        city_data = weather_data.get(
            city, {"temp": 20, "condition": "Unknown", "humidity": 50}
        )

        if units == "fahrenheit":
            city_data["temp"] = city_data["temp"] * 9 / 5 + 32

        return f"Weather in {city}: {city_data['condition']}, {city_data['temp']}°{'F' if units == 'fahrenheit' else 'C'}, {city_data['humidity']}% humidity"

    @tool
    def database_search(query: str, table: str = "products") -> str:
        """Search a mock database with detailed results."""
        # Mock database with different tables
        databases = {
            "products": [
                {"id": 1, "name": "Laptop", "price": 999, "category": "Electronics"},
                {"id": 2, "name": "Phone", "price": 699, "category": "Electronics"},
                {"id": 3, "name": "Desk", "price": 299, "category": "Furniture"},
                {"id": 4, "name": "Monitor", "price": 399, "category": "Electronics"},
                {"id": 5, "name": "Chair", "price": 199, "category": "Furniture"},
            ],
            "users": [
                {
                    "id": 1,
                    "name": "John Doe",
                    "email": "john@example.com",
                    "role": "admin",
                },
                {
                    "id": 2,
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "role": "user",
                },
            ],
        }

        data = databases.get(table, [])
        query_lower = query.lower()

        # Simple search implementation
        results = []
        for item in data:
            if any(query_lower in str(value).lower() for value in item.values()):
                results.append(item)

        if results:
            result_str = f"Found {len(results)} results in {table} table:\n"
            for item in results[:3]:  # Limit to 3 results
                result_str += f"- {item}\n"
            return result_str.strip()
        else:
            return f"No results found for '{query}' in {table} table"

    @tool
    def text_analyzer(text: str, analysis_type: str = "sentiment") -> str:
        """Analyze text with detailed insights."""
        text_length = len(text)
        word_count = len(text.split())

        if analysis_type == "sentiment":
            # Mock sentiment analysis
            positive_words = [
                "good",
                "great",
                "excellent",
                "amazing",
                "wonderful",
                "happy",
                "love",
            ]
            negative_words = [
                "bad",
                "terrible",
                "awful",
                "horrible",
                "sad",
                "angry",
                "hate",
            ]

            text_lower = text.lower()
            pos_count = sum(word in text_lower for word in positive_words)
            neg_count = sum(word in text_lower for word in negative_words)

            if pos_count > neg_count:
                sentiment = "Positive"
                confidence = "High" if pos_count >= 2 else "Medium"
            elif neg_count > pos_count:
                sentiment = "Negative"
                confidence = "High" if neg_count >= 2 else "Medium"
            else:
                sentiment = "Neutral"
                confidence = "Medium"

            return f"Text Analysis Results:\nText: '{text}'\nSentiment: {sentiment} ({confidence} confidence)\nPositive indicators: {pos_count}, Negative indicators: {neg_count}\nWord count: {word_count}, Character count: {text_length}"
        else:
            return (
                f"Analysis type '{analysis_type}' not supported. Available: sentiment"
            )

    return [calculator, weather_checker, database_search, text_analyzer]


def test_complete_agent_flows(tools):
    """Test complete agent flows that will show full tool execution"""
    print("\n" + "=" * 60)
    print("🧪 ENHANCED TEST: Complete Agent Tool Flows")
    print("=" * 60)

    try:
        from langchain.chat_models import init_chat_model
        from langchain.agents import create_tool_calling_agent, AgentExecutor
        from langchain_core.prompts import ChatPromptTemplate

        # Create model
        model = init_chat_model("gpt-4o-mini", temperature=0)

        # Create prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful assistant with access to various tools. Use them to provide comprehensive answers.",
                ),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        # Create agent
        agent = create_tool_calling_agent(model, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, tools=tools, verbose=True, return_intermediate_steps=True
        )

        # Test cases that will generate complete flows
        test_cases = [
            {
                "query": "What's 25 + 17? Please calculate this for me.",
                "description": "Simple math calculation",
            },
            # {
            #     "query": "What's the weather like in San Francisco?",
            #     "description": "Weather information lookup",
            # },
            # {
            #     "query": "Find all electronics in the products database",
            #     "description": "Database search with results",
            # },
            # {
            #     "query": "Analyze this text for sentiment: 'I absolutely love this amazing product! It's fantastic!'",
            #     "description": "Text analysis with detailed results",
            # },
            # {
            #     "query": "Calculate 15 * 7 and also check the weather in Tokyo",
            #     "description": "Multiple tool usage",
            # },
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 Test Case {i}: {test_case['description']}")
            print(f"📋 Query: {test_case['query']}")
            print("-" * 50)

            start_time = time.time()

            try:
                # This will generate multiple LLM calls:
                # 1. Initial call to decide which tools to use
                # 2. Tool execution (local)
                # 3. Final call to process results and respond
                result = agent_executor.invoke({"input": test_case["query"]})

                duration = time.time() - start_time
                print(f"⏱️  Total Duration: {duration:.2f}s")
                print(f"🎯 Final Result: {result['output']}")

                if "intermediate_steps" in result:
                    print(f"🔧 Intermediate Steps: {len(result['intermediate_steps'])}")

                # Add a small delay between tests
                time.sleep(1)

            except Exception as e:
                print(f"❌ Error in test case: {e}")
                import traceback

                traceback.print_exc()

        print("\n✅ Complete agent flow tests completed!")

    except Exception as e:
        print(f"❌ Error in complete flow test: {e}")
        import traceback

        traceback.print_exc()


def test_tracer_analysis():
    """Analyze what the tracer captured"""
    print("\n" + "=" * 60)
    print("📊 TRACER ANALYSIS")
    print("=" * 60)

    try:
        from langchain_tracer import get_http_tracer

        tracer = get_http_tracer()
        if not tracer:
            print("❌ No active tracer found")
            return

        # Get captured traces
        traces = tracer.get_session_traces()

        print(f"📈 Total Traces Captured: {len(traces)}")

        # Analyze trace types
        trace_types = {}
        tool_decisions = []
        final_responses = []
        tool_results = []

        for trace in traces:
            trace_type = trace.action_type
            trace_types[trace_type] = trace_types.get(trace_type, 0) + 1

            if trace.is_tool_call_step():
                tool_decisions.append(trace)
            if trace.is_final_response():
                final_responses.append(trace)
            if trace.has_tool_results():
                tool_results.append(trace)

        print(f"\n📋 Trace Type Breakdown:")
        for trace_type, count in trace_types.items():
            print(f"   • {trace_type}: {count}")

        print(f"\n🔧 Tool Decision Traces: {len(tool_decisions)}")
        for trace in tool_decisions:
            tools = ", ".join([tc.name for tc in trace.tool_calls])
            print(f"   • {trace.action_id[:8]}: {tools}")

        print(f"\n🎯 Final Response Traces: {len(final_responses)}")
        for trace in final_responses:
            response_preview = (
                trace.ai_response[:100] if trace.ai_response else "No response"
            )
            print(f"   • {trace.action_id[:8]}: {response_preview}...")

        print(f"\n📥 Traces with Tool Results: {len(tool_results)}")
        for trace in tool_results:
            results = ", ".join([tr.name for tr in trace.tool_responses])
            print(f"   • {trace.action_id[:8]}: {results}")

        # Cost and token analysis
        total_cost = sum(trace.cost_usd for trace in traces if trace.cost_usd)
        total_tokens = sum(
            trace.token_usage.total_tokens
            for trace in traces
            if trace.token_usage and trace.token_usage.total_tokens
        )

        print(f"\n💰 Cost Analysis:")
        print(f"   • Total Cost: ${total_cost:.6f}")
        print(f"   • Total Tokens: {total_tokens:,}")
        print(
            f"   • Average Cost per Trace: ${total_cost / len(traces):.6f}"
            if traces
            else "   • No traces"
        )

        # Export information
        stats = tracer.get_stats()
        print(f"\n📁 Export Information:")
        print(f"   • CSV File: {stats.get('file_path', 'Unknown')}")
        if stats.get("dashboard_url"):
            print(f"   • Dashboard: {stats['dashboard_url']}")

        print("\n💡 What to look for in the CSV:")
        print("   • Tool decision traces should show tool calls in output_data")
        print("   • Tool result traces should show tool responses in input_data")
        print("   • Final response traces should show complete answers")
        print("   • Each query should generate 2+ traces (decision + response)")

    except Exception as e:
        print(f"❌ Error in tracer analysis: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Main test function"""
    print("🚀 Enhanced Agent Breadcrumbs - Complete Tool Flow Test")
    print("=" * 60)
    print("This test captures the COMPLETE agent flow including:")
    print("✅ User queries")
    print("✅ LLM tool call decisions")
    print("✅ Tool execution results")
    print("✅ Final AI responses")
    print("✅ Token usage and costs")
    print()

    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set in environment")
        print("💡 Set your API key: export OPENAI_API_KEY='your-key-here'")
        print()

    # Setup enhanced tracing
    tracer = test_enhanced_http_tracer()
    if not tracer:
        print("❌ Failed to setup enhanced tracer. Exiting.")
        return

    # Create enhanced tools
    print("\n🔧 Creating enhanced test tools...")
    tools = create_enhanced_test_tools()
    print(f"✅ Created {len(tools)} tools: {[tool.name for tool in tools]}")

    try:
        # Run enhanced test suite
        test_complete_agent_flows(tools)

        # Wait a moment for all traces to be processed
        print("\n⏳ Waiting for traces to be processed...")
        time.sleep(2)

        # Analyze what was captured
        test_tracer_analysis()

        print("\n🎉 Enhanced testing completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Check enhanced_langchain_traces.csv for detailed logs")
        print("2. Open http://localhost:8080 for the dashboard")
        print(
            "3. Look for complete flows: query -> tool decision -> tool results -> final response"
        )

    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Cleanup
        if tracer:
            print("\n🧹 Cleaning up...")
            tracer.flush()  # Ensure all traces are written
            print("✅ Cleanup completed")


if __name__ == "__main__":
    main()
