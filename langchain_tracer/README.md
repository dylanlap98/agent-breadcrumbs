# Agent Breadcrumbs

A comprehensive observability library for AI agents and LLM applications. Track every decision, tool call, and interaction with complete transparency.

## 🎯 Two Approaches to Observability

Agent Breadcrumbs offers **two complementary approaches** for different use cases:

### 1. **Wrapper-Based Logging** (`agent_breadcrumbs.logger`)
**Best for**: Direct integration, custom frameworks, fine-grained control

```python
from agent_breadcrumbs import AgentLogger

logger = AgentLogger()
logger.log_llm_call(
    prompt="What is the weather?",
    response="Let me check that for you...",
    model_name="gpt-4"
)
```

### 2. **HTTP-Level Tracing** (`agent_breadcrumbs.tracer`) ⭐ **Recommended**
**Best for**: LangChain applications, complete data capture, zero code changes

```python
from agent_breadcrumbs.tracer import enable_http_tracing

# Enable tracing (one line of code)
enable_http_tracing()

# Use LangChain normally - everything gets traced automatically
from langchain.chat_models import ChatOpenAI
model = ChatOpenAI(model="gpt-4")
# All calls are now automatically traced with complete tool call data!
```

## 🚀 Quick Start

### Installation
```bash
pip install agent-breadcrumbs
```

### Basic Usage (HTTP Tracing - Recommended)
```python
from agent_breadcrumbs.tracer import enable_http_tracing
from langchain.chat_models import ChatOpenAI
from langchain.agents import create_openai_functions_agent

# Enable complete tracing
enable_http_tracing()

# Use LangChain normally - everything gets captured
model = ChatOpenAI(model="gpt-4")
response = model.invoke("What's 25 + 17?")

# View your traces
print("All traces saved to agent_traces.csv")
```

## 📊 What Gets Captured

### Complete LLM Interactions
- **User Queries**: Clean, extracted user input
- **Tool Calls**: Full tool name + arguments  
- **Tool Responses**: Complete results from each tool
- **AI Responses**: Final answers to users
- **Costs & Tokens**: Precise usage tracking

### Rich Metadata
- Session IDs for conversation tracking
- Timestamps and duration
- Model information
- Error handling and debugging info

## 🎨 Built-in Dashboard

Explore your traces with the built-in web dashboard:

```python
from agent_breadcrumbs.dashboard import start_dashboard

start_dashboard(port=8080)
# Open http://localhost:8080 to view traces
```

Features:
- Session-based conversation views
- Tool call flow visualization  
- Cost and token analytics
- Real-time monitoring

## 📁 Clean Output Format

Standardized CSV format perfect for analysis:

```csv
session_id,timestamp,user_query,tool_calls,tool_responses,ai_response,cost_usd,tokens
session_1,2025-07-27T10:30:00Z,"What's the weather in London?","[{""name"": ""get_weather"", ""args"": {""city"": ""London""}}]","[{""tool"": ""get_weather"", ""result"": ""Sunny, 72°F""}]","The weather in London is sunny and 72°F",0.0012,45
```

## 🤔 Which Approach Should I Use?

| Use Case | Recommended Approach | Why |
|----------|---------------------|-----|
| **LangChain Applications** | HTTP Tracing | Complete data, zero code changes, works with any LangChain version |
| **Production Monitoring** | HTTP Tracing | Captures everything, framework-agnostic |
| **Custom AI Frameworks** | Wrapper Logging | Fine-grained control, custom integration |
| **OpenAI Direct Usage** | Both work | HTTP tracing is simpler, wrapper gives more control |
| **Research & Analysis** | HTTP Tracing | Complete tool call lifecycle, no missing data |

## 🏗️ Why HTTP-Level Tracing?

**The Problem with Wrapper Approaches:**
- ❌ Framework-dependent integrations that break
- ❌ Incomplete tool call responses (like LangChain limitations)
- ❌ Missing data when frameworks change

**HTTP Tracing Solution:**
- ✅ Captures **all** data by intercepting API calls
- ✅ Framework-agnostic (works with any Python library)
- ✅ Complete tool call lifecycle
- ✅ Future-proof (doesn't break when frameworks update)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   LangChain     │────│  Agent           │────│   OpenAI API    │
│   Application   │    │  Breadcrumbs     │    │   (Raw Calls)   │
│                 │    │  (HTTP Tracer)   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Complete Traces │
                       │  (CSV/JSON)      │
                       └──────────────────┘
```

## 🔧 Configuration

```python
from agent_breadcrumbs.tracer import enable_http_tracing, TracerConfig

config = TracerConfig(
    output_file="my_traces.csv",
    dashboard_port=8080,
    trace_streaming=True,
    include_system_prompts=False
)

enable_http_tracing(config)
```

## 📊 Use Cases

- **Development**: Debug complex agent interactions
- **Production Monitoring**: Track costs and performance  
- **Training Data**: Generate high-quality SFT datasets
- **Analytics**: Understand user behavior and agent performance
- **Research**: Analyze AI decision-making patterns

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Agent Breadcrumbs** - Complete, reliable AI agent observability.