# FA Assistant

A RAG-based financial-advisor assistant. It's an internal research tool for an advisor
(not a client-facing product) that brings together three agents behind one chatbot:

1. **Structured data agent** ([src/structured_agent.py](src/structured_agent.py)) — reads
   client profiles, goals, and account/holdings data from [data/clients.json](data/clients.json).
2. **Conversation agent** ([src/conversation_agent.py](src/conversation_agent.py)) — semantic
   search (RAG) over past phone-call transcripts in [data/transcripts](data/transcripts), embedded
   with Voyage AI (`voyage-finance-2`) and stored in a local Chroma vector store.
3. **Market data agent** ([src/market_agent.py](src/market_agent.py)) — live security quotes,
   fundamentals, and news via `yfinance` (no API key required).

An orchestrator ([src/orchestrator.py](src/orchestrator.py)) runs a Claude tool-use loop that
decides which agent(s) to call for a given question, and a Streamlit app
([app.py](app.py)) provides the chat frontend.

All client and transcript data in this repo is **synthetic** — generated for demo purposes.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set:
- `ANTHROPIC_API_KEY` — https://console.anthropic.com/settings/keys
- `VOYAGE_API_KEY` — https://dash.voyageai.com/api-keys

## Run

```bash
streamlit run app.py
```

The first message you send will trigger a one-time embedding pass over the transcripts
(builds `chroma_db/` locally). Subsequent runs reuse the persisted index.

## Try asking

- "Which clients do I have and what's their risk tolerance?"
- "What's Maria Chen's portfolio look like, and what has she said in past calls about retirement?"
- "James Okafor is worried about his NVDA concentration — what's the current price doing, and what did we discuss last time?"
- "Summarize Linda Alvarez's estate planning conversation and check if JNJ has any recent news."

## Extending

- **Add a client:** append an entry to `data/clients.json`.
- **Add a transcript:** drop a `.txt` file in `data/transcripts/`, add a matching entry to
  `data/transcripts/manifest.json`. The index rebuilds automatically next run (it compares
  the manifest length to the Chroma collection size).
- **Swap models:** override `CLAUDE_MODEL` / `VOYAGE_EMBED_MODEL` in `.env`.
