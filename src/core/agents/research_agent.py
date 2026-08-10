"""
Handles company/market research and comparisons. Uses Claude's tool-use
loop to pull live data from the market data aggregator rather than
answering from the model's own (possibly stale) knowledge.
"""
from __future__ import annotations

from src.services.ai.llm_client import LLMClient
from src.services.ai.prompts.system_prompt import RESEARCH_SYSTEM_PROMPT
from src.services.market_data.aggregator import market_data

llm = LLMClient()

TOOLS = [
    {
        "name": "get_company_snapshot",
        "description": (
            "Get a live snapshot for a stock ticker: current quote/price change, "
            "company profile, and recent news. Use this whenever the user asks "
            "about a specific public company."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker symbol, e.g. AAPL"},
            },
            "required": ["symbol"],
        },
    }
]

async def _execute_tool(name: str, tool_input: dict) -> str:
    if name == "get_company_snapshot":
        snapshot = await market_data.get_company_snapshot(tool_input["symbol"])
        return str(snapshot)
    return "Unknown tool."


async def handle_research_request(message: str, conversation_history: list[dict], user_context: str) -> str:
    messages = [*conversation_history, {"role": "user", "content": message}]

    return await llm.complete_with_tool_loop(
        system=RESEARCH_SYSTEM_PROMPT.format(user_context=user_context),
        messages=messages,
        tools=TOOLS,
        tool_executor=_execute_tool,
    )
