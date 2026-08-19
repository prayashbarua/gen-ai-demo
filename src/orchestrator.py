"""Agentic tool-use loop that wires Claude to the three underlying agents."""
import json

import anthropic

from . import config, tools

SYSTEM_PROMPT = """You are an internal research assistant for a financial advisor \
(not for the advisor's clients directly). You help the advisor prepare for meetings \
and answer questions by pulling together three kinds of information via tools:

1. Structured client data — profiles, goals, accounts, and holdings.
2. Past phone-call transcripts — semantically searchable notes on what clients have said.
3. Live market data — current prices, fundamentals, and news for specific securities.

Guidelines:
- Use tools whenever a question depends on real client or market data — don't guess \
figures or fabricate holdings, quotes, or things a client supposedly said.
- When citing something from a past call, mention the date and topic so the advisor \
can verify it.
- Look up a client_id via list_clients if the advisor refers to a client by name only.
- You are supporting the advisor's own analysis and judgment. Frame portfolio \
observations as informational context for the advisor, not as directives, and note \
when something should be confirmed with the client directly.
- Be concise and structure multi-part answers with short headers or bullets.
"""

MAX_TOOL_ITERATIONS = 8


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def run_turn(messages: list[dict]) -> dict:
    """Run one user turn to completion, executing any tool calls Claude makes.

    `messages` is the full conversation history (mutated in place and returned).
    Returns {"text": final assistant text, "messages": updated history,
    "tool_calls": [{"name", "input", "result"}, ...] for UI transparency}.
    """
    client = _client()
    tool_calls_log = []
    response = None

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools.TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = tools.execute_tool(block.name, block.input)
                tool_calls_log.append(
                    {"name": block.name, "input": block.input, "result": result}
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str),
                    }
                )
        messages.append({"role": "user", "content": tool_results})
    else:
        return {
            "text": "I made too many tool calls trying to answer that — could you narrow the question?",
            "messages": messages,
            "tool_calls": tool_calls_log,
        }

    final_text = "".join(b.text for b in response.content if b.type == "text")
    return {"text": final_text, "messages": messages, "tool_calls": tool_calls_log}
