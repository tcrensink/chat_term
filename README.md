# ChatTerm
The fastest access to ChatGPT.

ChatTerm is a terminal-based TUI that provides instantaneous access to ChatGPT. Type `chat` to start or resume a terminal session.

# Installation
Requires python 3.5+, tmux, and an OPENAI_API_KEY

```bash
git clone https://github.com/tcrensink/chat_term.git
cd chat_term
python install.py
# open new shell session
```

# Usage
Terminal Commands:
```bash
chat # start or reconnect to chat_term session
chat restart # force restart chat_term session (when source is changed or error occurs)
chat stop # kills tmux chat_term session
chat --help # displays commands as described above
```

[Demo](https://user-images.githubusercontent.com/26497809/238851240-20f6f849-27f6-4e35-b6ef-e8ec761e63de.mov)
