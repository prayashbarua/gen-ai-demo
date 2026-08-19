"""Tool schemas exposed to Claude, and the dispatch map that executes them.

Each tool is backed by one of the three agents:
- structured_agent   -> client profiles, goals, accounts, holdings (structured data)
- conversation_agent -> semantic search over past phone-call transcripts (unstructured data)
- market_agent       -> live security prices / news from an external source
"""
from . import conversation_agent, market_agent, structured_agent

TOOLS = [
    {
        "name": "list_clients",
        "description": "List all clients with their id, name, and risk tolerance.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_client_profile",
        "description": (
            "Get a client's full profile: demographics, risk tolerance, investment "
            "goals, advisor notes, and account balances. Use this for questions about "
            "who the client is, their goals, or overall financial picture."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "Client id, e.g. 'C001'."}
            },
            "required": ["client_id"],
        },
    },
    {
        "name": "get_client_holdings",
        "description": (
            "Get the detailed account-by-account holdings (tickers, share counts, "
            "cost basis) for a client. Use this for questions about specific positions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "Client id, e.g. 'C001'."}
            },
            "required": ["client_id"],
        },
    },
    {
        "name": "search_client_conversations",
        "description": (
            "Semantically search past client phone-call transcripts for relevant "
            "context — concerns raised, life events, goals mentioned, prior advice "
            "given. Use this for anything about what a client has said in past calls."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for, e.g. 'concerns about market volatility'.",
                },
                "client_id": {
                    "type": "string",
                    "description": "Optional client id to restrict the search to one client's calls.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Max number of matching excerpts to return (default 5).",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_security_quote",
        "description": (
            "Get the current price, day/year range, and key fundamentals (P/E, "
            "dividend yield, sector) for a stock or ETF ticker."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Ticker symbol, e.g. 'AAPL'."}
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_security_news",
        "description": "Get recent news headlines for a stock or ETF ticker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Ticker symbol, e.g. 'AAPL'."},
                "max_items": {
                    "type": "integer",
                    "description": "Max number of headlines to return (default 5).",
                },
            },
            "required": ["ticker"],
        },
    },
]

_DISPATCH = {
    "list_clients": lambda **kw: structured_agent.list_clients(),
    "get_client_profile": lambda **kw: structured_agent.get_client_profile(**kw),
    "get_client_holdings": lambda **kw: structured_agent.get_client_holdings(**kw),
    "search_client_conversations": lambda **kw: conversation_agent.search_client_conversations(**kw),
    "get_security_quote": lambda **kw: market_agent.get_security_quote(**kw),
    "get_security_news": lambda **kw: market_agent.get_security_news(**kw),
}


def execute_tool(name: str, tool_input: dict):
    """Dispatch a Claude tool call to the backing agent function."""
    if name not in _DISPATCH:
        return {"error": f"Unknown tool '{name}'"}
    try:
        return _DISPATCH[name](**tool_input)
    except Exception as e:
        return {"error": f"Tool '{name}' failed: {e}"}
