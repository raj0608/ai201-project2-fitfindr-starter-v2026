# 👗 Project 2 — FitFindr AI Agent: Skills & Technologies

> **Note:** This is a personal portfolio reflection. The graded submission is `README.md`.

---

## 🔍 What I Built

A **tool-calling AI agent** for thrift and resale fashion. A user describes what they want in plain language ("a vintage graphic tee under $30, size M") and FitFindr searches listings data, picks the best match, generates an outfit suggestion using the user's wardrobe, and writes a shareable fit caption. If nothing matches, it says so cleanly instead of guessing.

The project introduced **Model Context Protocol (MCP)** — moving one tool out of the local process and into a separately hosted server so that any MCP-compatible client could call it.

---

## 🛠️ Tools & Technologies

| Category | Tool / Library | Purpose |
|---|---|---|
| **LLM API** | Google Gemini (`google-genai` ≥1.0) | Outfit suggestions and fit-card caption generation |
| **Agent Protocol** | MCP (`mcp` ≥1.0) | Exposes `search_listings` as a remotely callable tool |
| **Web Server** | Flask + Gunicorn | HTTP API via `serve.py` for deployment |
| **Env Management** | python-dotenv | Loads API keys from `.env` |
| **Language** | Python 3.11–3.13 | Core implementation language |

---

## ⚙️ Architecture & Key Design Decisions

- **Planning loop** (`agent.py`) — The agent inspects the result of each tool call before deciding the next step. If `search_listings` returns an empty list, it stores an informative error message in the session and stops — it never calls `suggest_outfit` on nothing.
- **Tool separation** — `search_listings` is a pure data-filter function (no model call); `suggest_outfit` and `create_fit_card` both call Gemini. This separation made it natural to expose `search_listings` via MCP without latency concerns.
- **MCP server/client split** — `mcp_server.py` registers `search_listings` with a typed schema and a description written for external consumers. `mcp_client.py` calls it over the protocol, keeping the agent decoupled from the tool implementation.
- **Regex-based query parsing** — `_parse_query()` extracts `max_price` and `size` from free-text queries before dispatching to the search tool, keeping the LLM out of structured-extraction work it doesn't need to do.
- **Fallback guarantees** — Every tool has a defined empty/error return: `search_listings` returns `[]`, `suggest_outfit` returns a hardcoded sentence if the model returns nothing, `create_fit_card` handles an empty outfit string without raising.

---

## 🧠 Skills Learned

### AI / ML Concepts
- What makes a pipeline an **agent**: inspecting tool output before picking the next action (branching), vs. a fixed sequence of function calls
- Designing tool contracts: typed inputs, documented empty/error cases, and descriptions written for external consumers rather than internal callers
- How MCP standardises tool exposure so any MCP-compatible client can call your tool without knowing your code
- Prompting for structured creative output (captions, outfit suggestions) with predictable format constraints

### Software Engineering
- Implementing a planning loop with session state (`session["selected_item"]`, `session["error"]`)
- Writing an MCP server with typed tool schemas and a client that calls it over the protocol
- Regex-based natural-language parsing to extract structured fields (price, size) from free-text queries
- Graceful degradation: every code path returns something usable, never `None` or an unhandled exception

### Tools & Workflow
- Google Gemini API for generative tasks
- MCP SDK (`mcp` package) — server registration, tool schema definition, client invocation
- `trace.py` — tracing agent decisions for debugging the planning loop
- Flask + Gunicorn for HTTP deployment
- Evaluation with `run_eval.py` and scenario-driven test cases (`scenarios.py`)

---

## 📂 Key Files

| File | Role |
|---|---|
| `agent.py` | Planning loop — decides which tool to call next |
| `tools.py` | `suggest_outfit` and `create_fit_card` tool implementations |
| `mcp_server.py` | MCP server exposing `search_listings` with a typed schema |
| `mcp_client.py` | MCP client the agent uses to call the remote tool |
| `generate.py` | Gemini API wrapper shared by the two LLM tools |
| `trace.py` | Decision tracer for debugging the agent loop |
| `scenarios.py` | Test scenarios for evaluation |
| `run_eval.py` | Automated evaluation runner |
| `serve.py` | Flask HTTP server wrapping the agent |
| `config.py` | Centralised configuration constants |
