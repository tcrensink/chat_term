# Chat Term
A TUI for optimized access to the ChatGPT API

# Installation
Requires python 3.5+, `tmux`, and an `OPENAI_API_KEY`

```bash
git clone https://github.com/tcrensink/chat_term.git
cd chat_term
python install.py
```
`install.py` adds a `chat` shell function, stores your api key in `secrets.json`.

# Usage
The `chat` command will connect to a tmux instance running `chat_term`; press `ctrl-c` to disconnect.
