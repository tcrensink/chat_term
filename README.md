# Chat Term
Fast terminal access to ChatGPT.

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

[Demo](https://user-images.githubusercontent.com/26497809/238851240-20f6f849-27f6-4e35-b6ef-e8ec761e63de.mov)
