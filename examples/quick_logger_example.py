from agent_breadcrumbs import quick_logger

# Create logger (saves to agent_breadcrumbs.csv)
logger = quick_logger()

# Log LLM interactions
logger.log_llm_call(
    prompt="What is the capital of France?",
    response="The capital of France is Paris.",
    model_name="gpt-4",
    token_count=25,
)

# Log tool usage
logger.log_tool_use(
    tool_name="web_search",
    tool_input={"query": "weather today"},
    tool_output={"temperature": "72F", "condition": "sunny"},
)

# Log reasoning steps
logger.log_reasoning(
    thought_process="User is asking about weather, I should search for current conditions",
    decision="Use web_search tool with query 'weather today'",
)
