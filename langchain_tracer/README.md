# Agent Breadcrumbs HTTP Tracer

**Complete, framework-agnostic LLM observability through HTTP-level interception**

The HTTP Tracer is the next evolution of Agent Breadcrumbs, solving the fundamental limitations of wrapper-based approaches by intercepting HTTP calls directly to LLM providers.

## 🎯 Why HTTP-Level Tracing?

### The Problem with Wrapper Approaches
- ❌ **Incomplete Tool Call Data**: LangChain and other frameworks don't expose complete tool call information through their public APIs
- ❌ **Framework Dependencies**: Wrappers break when frameworks update their internal structures  
- ❌ **Missing Internal Operations**: Many LLM interactions happen internally and aren't captured
- ❌ **Complex Integration**: Requires framework-specific knowledge and constant maintenance

### The HTTP Tracing Solution
- ✅ **Complete Data Capture**: Intercepts raw HTTP calls to capture 100% of tool calls, responses, and metadata
- ✅ **Framework Agnostic**: Works with LangChain, direct OpenAI, LlamaIndex, or any Python LLM library
- ✅ **Zero Code Changes**: Enable with one line of code, no refactoring required
- ✅ **Future Proof**: Doesn't break when frameworks change their internal APIs

## 🚀 Quick Start

### Installation
```bash
# Core functionality
pip install requests  # or httpx for async support

# Optional: Dashboard dependencies  
pip install flask flask-cors
```

### Basic Usage
```python
from langchain_tracer import enable_http_tracing

# Enable tracing - that's it!
enable_http_tracing()

# Use any LLM library normally - everything gets traced
from langchain.chat_models import ChatOpenAI
model = ChatOpenAI(model="gpt-4o-mini")
response = model.invoke("What's the weather like?")

print("✅ All traces saved to agent_traces.csv")
```

### With Tool Calls (The Key Advantage)
```python
from langchain_tracer import enable_http_tracing
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.tools import DuckDuckGoSearchRun

# Enable complete tracing
enable_http_tracing()

# Create agent with tools
model = ChatOpenAI(model="gpt-4o-mini")
search = DuckDuckGoSearchRun()
agent = create_openai_functions_agent(model, [search], prompt)
executor = AgentExecutor(agent=agent, tools=[search])

# This complex interaction will be FULLY traced including:
# - Original user query
# - Tool call decisions  
# - Tool call arguments
# - Tool responses
# - Final AI response
result = executor.invoke({"input": "What's the latest AI news?"})

# All tool calls captured automatically! 🎉
```

## 📊 What Gets Captured

### Complete LLM Interaction Data
```csv
session_id,timestamp,user_input,tool_calls,tool_responses,ai_response,cost_usd,tokens
session_123,2025-07-27T10:30:00Z,"What's the weather?","[{""name"": ""get_weather"", ""args"": {""city"": ""London""}}]","[{""result"": ""Sunny, 72°F""}]","The weather is sunny and 72°F",0.0012,45
```

### Rich Metadata
- **Session IDs**: Track conversation flows
- **Timestamps**: Precise timing information  
- **Token Usage**: Prompt, completion, and total tokens
- **Cost Tracking**: Automatic cost calculation
- **Duration**: Response time measurements
- **Provider Info**: Model names and API providers
- **Raw Data**: Complete request/response for debugging

## 🔧 Advanced Configuration

```python
from langchain_tracer import enable_http_tracing, TracerConfig

config = TracerConfig(
    # Output settings
    output_file="my_traces.csv",
    output_format="csv",  # csv, json, jsonl
    
    # Session management
    session_id="production_session_1",
    auto_session=True,
    
    # Capture settings
    capture_tool_calls=True,
    capture_tool_responses=True,
    include_system_prompts=True,
    
    # Dashboard
    dashboard_enabled=True,
    dashboard_port=8080,
    
    # Performance
    async_logging=True,
    buffer_size=100,
    flush_interval=5.0,
    
    # Filtering
    min_token_threshold=10,
    exclude_endpoints=["health", "status"],
)

tracer = enable_http_tracing(config)
```

## 📊 Built-in Dashboard

View your traces with the integrated dashboard:

```python
# Dashboard starts automatically (if enabled in config)
enable_http_tracing()

# Or start manually
from langchain_tracer.dashboard import start_dashboard
start_dashboard(port=8080)
```

**Dashboard Features:**
- 🔍 **Session Explorer**: Browse conversations by session
- 🔧 **Tool Call Visualization**: See complete tool interaction flows  
- 📈 **Cost Analytics**: Track spending across models and sessions
- ⚡ **Performance Metrics**: Response times and token usage
- 📱 **Responsive Design**: Works on desktop and mobile

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Any Python   │    │  HTTP Tracer     │    │   LLM Provider  │
│   LLM Library   │────│  (Intercepts)    │────│   (OpenAI,      │
│   (LangChain,   │    │                  │    │    Anthropic)   │
│    OpenAI, etc) │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Storage Layer   │
                       │  (CSV/JSON)      │
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Dashboard      │
                       │   (Optional)     │
                       └──────────────────┘
```

## 🎛️ API Reference

### Core Functions

```python
# Enable tracing
tracer = enable_http_tracing(config=None, storage=None)

# Session management
tracer.new_session() -> str
tracer.set_session(session_id: str)

# Data access
tracer.get_session_traces(session_id: str) -> List[TraceEvent]
tracer.get_all_traces() -> List[TraceEvent]
tracer.get_sessions() -> List[str]

# Export
tracer.export_traces(format="csv", output_file=None) -> str

# Control
tracer.flush()  # Force write buffered traces
tracer.print_summary()  # Print statistics
tracer.stop()  # Stop tracing and cleanup
```

### Storage Backends

```python
# CSV Storage (default, dashboard compatible)
from langchain_tracer.storage import CSVStorage
storage = CSVStorage("traces.csv", buffer_size=100)

# JSON Storage (richer data structure)
from langchain_tracer.storage import JSONStorage
storage = JSONStorage("traces.jsonl", format_type="jsonl")

# Custom storage
class CustomStorage:
    def store_trace(self, trace: TraceEvent): pass
    def load_traces(self, session_id=None): pass
    def flush(self): pass
```

## 🔍 Framework Compatibility

**Tested and Working:**
- ✅ **LangChain** (all versions) - Complete tool call capture
- ✅ **OpenAI Python SDK** - Direct API calls  
- ✅ **LlamaIndex** - Query engines and agents
- ✅ **Haystack** - Pipeline operations
- ✅ **Custom Applications** - Any HTTP-based LLM calls

**Example Multi-Framework Usage:**
```python
enable_http_tracing()

# All of these will be traced automatically:

# 1. Direct OpenAI
import openai
client = openai.OpenAI()
client.chat.completions.create(model="gpt-4", messages=[...])

# 2. LangChain  
from langchain.chat_models import ChatOpenAI
ChatOpenAI().invoke("Hello")

# 3. LlamaIndex
from llama_index.llms import OpenAI
OpenAI().complete("Hello")

# All calls captured with the same unified format! 🎉
```

## 🛡️ Production Considerations

### Performance
- **Minimal Overhead**: ~1-2ms per request
- **Async Buffering**: Non-blocking writes to storage
- **Memory Efficient**: Configurable buffer sizes
- **Auto-Flushing**: Prevents data loss

### Security
```python
config = TracerConfig(
    # Privacy options
    redact_sensitive_data=True,
    sensitive_patterns=['api_key', 'password', 'token'],
    
    # Data filtering
    include_system_prompts=False,  # Exclude system prompts
    min_token_threshold=50,        # Only log substantial calls
)
```

### Monitoring Integration
```python
# Custom storage for monitoring systems
class DataDogStorage:
    def store_trace(self, trace):
        # Send metrics to DataDog
        statsd.increment('llm.calls')
        statsd.histogram('llm.duration', trace.duration_ms)
        statsd.histogram('llm.cost', trace.cost_usd)
        
        # Also store locally
        self.csv_storage.store_trace(trace)

enable_http_tracing(storage=DataDogStorage())
```

## 🔄 Migration from Wrapper Approach

### Before (Wrapper-based logging)
```python
from agent_breadcrumbs import AgentLogger

logger = AgentLogger()

# Manual logging required for each call
response = model.invoke(prompt)
logger.log_llm_call(
    prompt=prompt,
    response=response.content,
    model_name="gpt-4"
)
# ❌ Tool calls not captured
# ❌ Framework-dependent
# ❌ Easy to miss calls
```

### After (HTTP Tracing)
```python
from langchain_tracer import enable_http_tracing

enable_http_tracing()

# Everything traced automatically
response = model.invoke(prompt)
# ✅ Complete tool calls captured
# ✅ Framework-agnostic  
# ✅ Never miss a call
```

## 🧪 Testing

```bash
# Run the test suite
python test_tracer.py

# Test with example usage
python example_usage.py
```

## 📈 Roadmap

- [ ] **Streaming Support**: Real-time trace updates for streaming responses
- [ ] **More Providers**: Anthropic, Cohere, HuggingFace direct support  
- [ ] **Advanced Analytics**: Query performance analysis, cost optimization
- [ ] **Cloud Integrations**: Direct export to observability platforms
- [ ] **Enterprise Features**: Role-based access, audit logs, retention policies

## 🤝 Contributing

The HTTP Tracer is designed to be easily extensible:

1. **Storage Backends**: Implement custom storage for your infrastructure
2. **Provider Support**: Add parsers for new LLM providers
3. **Dashboard Features**: Enhance the React dashboard
4. **Integrations**: Connect to monitoring and analytics platforms

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details.

---

**HTTP Tracer** - Complete, reliable, framework-agnostic LLM observability.

*Finally, see everything your AI agents are actually doing.* 🔍✨