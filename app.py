"""Streamlit chatbot frontend for the FA Assistant."""
import streamlit as st

from src import config, orchestrator, structured_agent

st.set_page_config(page_title="FA Assistant", page_icon="💼", layout="wide")


def render_text(text: str) -> None:
    """st.markdown treats bare $...$ as LaTeX math, which mangles dollar amounts."""
    st.markdown(text.replace("$", "\\$"))

if not config.ANTHROPIC_API_KEY or not config.VOYAGE_API_KEY:
    st.error(
        "Missing API keys. Copy `.env.example` to `.env` and set "
        "`ANTHROPIC_API_KEY` and `VOYAGE_API_KEY` before running the app."
    )
    st.stop()

if "api_messages" not in st.session_state:
    st.session_state.api_messages = []  # full history sent to Claude (tool blocks included)
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []  # [{"role", "text", "tool_calls"}] for rendering

with st.sidebar:
    st.header("Clients")
    for c in structured_agent.list_clients():
        st.markdown(f"**{c['name']}** ({c['client_id']}) — {c['risk_tolerance']}")
    st.divider()
    if st.button("Clear conversation"):
        st.session_state.api_messages = []
        st.session_state.display_messages = []
        st.rerun()

st.title("💼 FA Assistant")
st.caption(
    "Internal research assistant — pulls client profiles, past call notes, "
    "and live market data to help you prep and answer questions."
)

for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        render_text(msg["text"])
        if msg.get("tool_calls"):
            with st.expander(f"🔧 {len(msg['tool_calls'])} tool call(s) used"):
                for call in msg["tool_calls"]:
                    st.markdown(f"**{call['name']}**`({call['input']})`")
                    st.json(call["result"])

user_input = st.chat_input("Ask about a client, a past call, or a security...")

if user_input:
    st.session_state.display_messages.append({"role": "user", "text": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.api_messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = orchestrator.run_turn(st.session_state.api_messages)
        render_text(result["text"])
        if result["tool_calls"]:
            with st.expander(f"🔧 {len(result['tool_calls'])} tool call(s) used"):
                for call in result["tool_calls"]:
                    st.markdown(f"**{call['name']}**`({call['input']})`")
                    st.json(call["result"])

    st.session_state.api_messages = result["messages"]
    st.session_state.display_messages.append(
        {"role": "assistant", "text": result["text"], "tool_calls": result["tool_calls"]}
    )
