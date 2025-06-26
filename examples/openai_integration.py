import openai
import json
from agent_breadcrumbs import AgentLogger


class LoggedOpenAI:
    """Wrapper around OpenAI client with automatic logging"""

    def __init__(self, api_key: str, logger: AgentLogger = None):
        self.client = openai.OpenAI(api_key=api_key)
        self.logger = logger or AgentLogger()

    def chat_completion(self, messages, model="gpt-4o", **kwargs):
        # Log the request
        prompt = json.dumps(messages)

        # Make the API call
        response = self.client.chat.completions.create(
            messages=messages, model=model, **kwargs
        )

        # Log the response
        self.logger.log_llm_call(
            prompt=prompt,
            response=response.choices[0].message.content,
            model_name=model,
            token_count=response.usage.total_tokens if response.usage else None,
        )

        return response


# Usage
logged_openai = LoggedOpenAI(api_key="your-key")
response = logged_openai.chat_completion(
    [{"role": "user", "content": "Hello, how are you?"}]
)
