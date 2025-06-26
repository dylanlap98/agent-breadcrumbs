from agent_breadcrumbs import AgentLogger

# Initialize logger (creates agent_logs.csv in current directory)
logger = AgentLogger()

# Log an LLM call
logger.log_llm_call(
    prompt="What is the capital of France?",
    response="The capital of France is Paris.",
    model_name="gpt-4o",
    token_count=25,
)

# Log tool usage
logger.log_tool_use(
    tool_name="web_search",
    tool_input={"query": "weather today"},
    tool_output={"temperature": "72F", "condition": "sunny"},
)

# Log reasoning
logger.log_reasoning(
    thought_process="User is asking about weather, I should use web search",
    decision="Call web_search tool with query 'weather today'",
)

# View session history
history = logger.get_session_history()
for action in history:
    print(f"{action.timestamp}: {action.action_type}")
