from pydantic_ai import Agent
from infrastructure.llm_client import get_model

summary_agent = Agent(
    model=get_model(),
    output_type=str,
    system_prompt=(
        "You summarize command execution results in 1-3 short, friendly sentences. "
        "Respond in the same language the user used. "
        "If some steps were skipped due to a prior failure, mention it briefly. "
        "If retries were exhausted without success, say so clearly."
    ),
)
