"""
LangGraph Supervisor + Workers Demo
====================================
Goal: learn the core LangGraph building blocks by building a tiny
multi-agent system from scratch.

Architecture:

        ┌─────────────┐
        │  Supervisor  │  <-- decides which worker acts next
        └──────┬───────┘
         ┌──────┴──────┐
         ▼             ▼
   ┌───────────┐  ┌──────────┐
   │ Researcher │  │  Writer  │
   └───────────┘  └──────────┘

Flow: user asks a question -> Supervisor routes to Researcher to
gather info -> control returns to Supervisor -> Supervisor routes to
Writer to compose the final answer -> Supervisor sees the task is
done -> graph ends (FINISH).

This is the same pattern used in real orchestration systems: a
central router node + specialist worker nodes + a shared state object
that flows through the graph.
"""

import os
from typing import Literal, TypedDict, Annotated

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages


# ---------------------------------------------------------------------------
# 1. STATE
# ---------------------------------------------------------------------------
# Every LangGraph app is built around a shared "state" object that gets
# passed between nodes. Each node reads from it and returns updates to it.
#
# `add_messages` is a special reducer: instead of overwriting the messages
# list on each update, it APPENDS new messages to it. This is how
# conversation history accumulates across nodes.

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next: str  # which node the supervisor wants to run next


# ---------------------------------------------------------------------------
# 2. LLM SETUP
# ---------------------------------------------------------------------------
# Groq is free to sign up for at https://console.groq.com
# Once you have a key: export GROQ_API_KEY="your-key-here"
# llama-3.3-70b-versatile is a good free-tier model: fast and capable enough
# for this kind of routing/reasoning task.

model_name = os.environ.get("GROQ_MODEL", "groq/compound-mini")
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("Set GROQ_API_KEY before running this script.")

llm = ChatGroq(
    model=model_name,
    temperature=0,
    api_key=api_key,
)


def invoke_with_user_tail(messages):
    """Groq requires the final message in a chat request to be from the user."""
    convo = list(messages)
    if not convo or convo[-1].type != "human":
        convo.append(HumanMessage(content="Continue based on the conversation above."))
    return llm.invoke(convo)


# ---------------------------------------------------------------------------
# 3. WORKER NODES
# ---------------------------------------------------------------------------
# A node is just a function: (state) -> partial state update.
# Each worker gets the full message history so far, does its job, and
# appends its own response.

def researcher_node(state: AgentState) -> dict:
    """Gathers/reasons about facts relevant to the user's question.
    In a real system this node would also call actual tools (web search,
    a database, an API). Here it just reasons using the LLM so you can see
    the routing mechanics clearly before adding tool complexity."""

    system_prompt = SystemMessage(content=(
        "You are a Research agent. Given the conversation so far, produce "
        "a concise set of relevant facts or considerations on the topic. "
        "Do not write a final answer - just gather and list what's relevant. "
        "Prefix your response with 'RESEARCH NOTES:'."
    ))
    response = invoke_with_user_tail([system_prompt] + state["messages"])
    return {"messages": [AIMessage(content=response.content, name="researcher")]}


def writer_node(state: AgentState) -> dict:
    """Takes everything gathered so far and writes the final user-facing
    answer."""

    system_prompt = SystemMessage(content=(
        "You are a Writer agent. Using the research notes already present "
        "in the conversation, write a clear, final answer for the user. "
        "Prefix your response with 'FINAL ANSWER:'."
    ))
    response = invoke_with_user_tail([system_prompt] + state["messages"])
    return {"messages": [AIMessage(content=response.content, name="writer")]}


# ---------------------------------------------------------------------------
# 4. SUPERVISOR NODE
# ---------------------------------------------------------------------------
# The supervisor's only job is to look at the conversation and decide who
# should act next: "researcher", "writer", or "FINISH".
#
# We force it to respond with exactly one of those words so we can route
# programmatically - this is the core trick behind supervisor patterns.

WORKERS = ["researcher", "writer"]
OPTIONS = WORKERS + ["FINISH"]


def supervisor_node(state: AgentState) -> dict:
    system_prompt = SystemMessage(content=(
        f"You are a Supervisor managing these workers: {WORKERS}.\n"
        "Given the conversation, decide who should act next.\n"
        "- If there are no RESEARCH NOTES yet, choose 'researcher'.\n"
        "- If there are RESEARCH NOTES but no FINAL ANSWER yet, choose 'writer'.\n"
        "- If there is already a FINAL ANSWER, choose 'FINISH'.\n"
        f"Respond with exactly one word from this list: {OPTIONS}. "
        "No punctuation, no explanation - just the word."
    ))
    response = invoke_with_user_tail([system_prompt] + state["messages"])
    choice = response.content.strip()

    # simple safety net in case the model doesn't follow instructions exactly
    if choice not in OPTIONS:
        choice = "FINISH"

    return {"next": choice}


# ---------------------------------------------------------------------------
# 5. ROUTING LOGIC
# ---------------------------------------------------------------------------
# LangGraph needs an explicit function to translate state["next"] into an
# actual edge to follow. This is a "conditional edge."

def route(state: AgentState) -> Literal["researcher", "writer", "__end__"]:
    if state["next"] == "FINISH":
        return "__end__"
    return state["next"]


# ---------------------------------------------------------------------------
# 6. BUILD THE GRAPH
# ---------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("writer", writer_node)

    # Every worker reports back to the supervisor after acting
    graph.add_edge("researcher", "supervisor")
    graph.add_edge("writer", "supervisor")

    # The supervisor's next step is decided dynamically
    graph.add_conditional_edges(
        "supervisor",
        route,
        {"researcher": "researcher", "writer": "writer", "__end__": END},
    )

    graph.set_entry_point("supervisor")

    return graph.compile()


# ---------------------------------------------------------------------------
# 7. RUN IT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = build_graph()

    user_question = "What is machine learning?"

    result = app.invoke(
        {"messages": [HumanMessage(content=user_question)], "next": ""},
        config={"recursion_limit": 10},
    )

    print("\n=== FULL CONVERSATION TRACE ===\n")
    for msg in result["messages"]:
        speaker = getattr(msg, "name", None) or msg.type
        print(f"[{speaker}]\n{msg.content}\n")
