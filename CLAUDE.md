# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

ChatTerm is a terminal LLM chat client built with [Textual](https://textual.textualize.io/) (TUI framework) and managed via tmux. It uses the OpenAI-compatible API so it works with OpenAI, Anthropic (via compatibility endpoint), vLLM, Ollama, and others.

## Commands

```bash
# Install dependencies
uv sync

# Run the app directly (without tmux)
uv run app.py

# Run via tmux wrapper (normal usage)
./run.sh           # start or attach to chat_term session
./run.sh restart   # kill and restart session
./run.sh stop      # kill session

# Run tests (parse_utils has inline tests)
uv run pytest parse_utils.py
```

## Architecture

The app is intentionally minimal with flat structure at the repo root:

- **`app.py`** — the entire TUI application. `ChatApp` (Textual `App` subclass) owns `chat_history`, renders widgets for each user/assistant turn, and streams responses via `AsyncOpenAI`. Config and keybindings are loaded at module import time.
- **`parse_utils.py`** — parses streaming markdown into alternating text/code blocks. Monkey-patches `marko.block.FencedCode` to track character positions (`start`/`end`) so raw text spans can be extracted alongside display text. `parse_text()` returns a list of `{raw_text, display_text, type}` dicts.
- **`run.sh`** — tmux wrapper: creates a `chat_term` named session, runs `uv run app.py`, and auto-kills the session on error.
- **`config.json`** — model configurations (model name, base_url, system prompt). Uses JS-style `//` comments stripped at load time. Set `active_model_config` to switch models.
- **`secrets.json`** — API keys keyed by model config name (e.g. `"claude"`, `"gpt-4o"`).
- **`chat.css`** — Textual CSS for widget layout and styling.
- **`chat_term/compute_server.py`** — unused/experimental FastAPI server that exposes a Python code execution endpoint for LLM tool use.

## Key Design Patterns

**Streaming render loop** (`app.py:render_response`): On each streamed chunk, `parse_text()` re-parses the accumulated text. Widgets are created lazily on first output and the "current" widget is updated in-place until a new block type (code vs text) starts, then a new widget is mounted.

**Config loading**: `config.json` supports `//` comments; they are stripped with a line filter before `json.loads()`. The active model config is resolved at startup into `CONFIG["model_config"]`.

**Click-to-copy**: Both `ResponseText` and `ResponseCode` widgets copy their `_display_text` to clipboard on click, with a brief opacity animation as feedback.

**Keybindings**: Defined in `config.json` as `[key, action, description]` triples. The `quit` binding in config must match the tmux detach key in `tmux.conf` (both default to `ctrl+x`).
