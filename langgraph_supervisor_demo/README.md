# LangGraph Supervisor Demo

This directory contains implementations of a multi-agent system using LangGraph with different LLM providers.

## Files

### Groq Version
- **`supervisor_demo_groq.py`** - Groq API implementation
  - Uses: `langchain_groq.ChatGroq`
  - Model: `groq/compound-mini` (default, configurable)
  - API Key: `GROQ_API_KEY`
  - Setup: `export GROQ_API_KEY="your-key-here"`

### Gemini Version
- **`supervisor_demo_gemini.py`** - Google Gemini API implementation
  - Uses: `langchain_google_genai.ChatGoogleGenerativeAI`
  - Model: `gemini-2.0-flash` (default, configurable)
  - API Key: `GOOGLE_API_KEY`
  - Setup: `export GOOGLE_API_KEY="your-key-here"`

- **`supervisor_demo_gemini.ipynb`** - Jupyter notebook for Gemini version
  - Interactive cells demonstrating each component
  - Step-by-step architecture explanation
  - Easy testing and modification

## Architecture

```
        ┌─────────────┐
        │  Supervisor  │  <-- decides which worker acts next
        └──────┬───────┘
         ┌──────┴──────┐
         ▼             ▼
   ┌───────────┐  ┌──────────┐
   │ Researcher │  │  Writer  │
   └───────────┘  └──────────┘
```

The Supervisor routes between Researcher (gathers facts) and Writer (composes answer).

## Running the Examples

### Prerequisites

```bash
pip install langgraph langchain-groq langchain-google-genai langchain-core
```

### Running Groq Version

```bash
export GROQ_API_KEY="your-groq-key-here"
python supervisor_demo_groq.py
```

Optionally customize the model:
```bash
export GROQ_MODEL="groq/compound-mini"  # or other available models
python supervisor_demo_groq.py
```

### Running Gemini Version

```bash
export GOOGLE_API_KEY="your-gemini-key-here"
python supervisor_demo_gemini.py
```

Optionally customize the model:
```bash
export GEMINI_MODEL="gemini-2.0-flash"  # or other Gemini models
python supervisor_demo_gemini.py
```

### Running Jupyter Notebook

```bash
jupyter notebook supervisor_demo_gemini.ipynb
```

Then run the cells to see step-by-step execution with explanations.

## Key Concepts

1. **State Object**: Shared state passed between nodes with message history
2. **Message Reducer**: `add_messages` appends messages instead of overwriting
3. **Worker Nodes**: Specialist agents (researcher, writer) that process state
4. **Supervisor Node**: Central router that decides which worker acts next
5. **Conditional Edges**: Dynamic routing based on supervisor's decision
6. **Graph Compilation**: LangGraph compiles nodes and edges into executable workflow

## Comparing Providers

| Feature | Groq | Gemini |
|---------|------|--------|
| Speed | Very Fast | Fast |
| API Key | GROQ_API_KEY | GOOGLE_API_KEY |
| Default Model | groq/compound-mini | gemini-2.0-flash |
| Free Tier | Yes | Yes |
| Token Limits | Rate-limited (TPM) | Rate-limited (TPM) |
| Setup | Easy | Easy |

## Customization

Edit the `user_question` at the bottom of either script to test different queries:

```python
user_question = "Your custom question here"
```

## Troubleshooting

**Rate Limit Errors**:
- Wait a moment before retrying
- Use smaller models or simpler questions to reduce token usage

**API Key Issues**:
- Verify your environment variable is set: `echo $GROQ_API_KEY` or `echo $GOOGLE_API_KEY`
- Check that your key is valid and has not expired

**Import Errors**:
- Ensure all packages are installed: `pip install -r requirements.txt`
- Verify Python version (3.8+)
