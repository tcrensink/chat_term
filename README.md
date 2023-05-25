# ChatTerm
The fastest access to ChatGPT.

`ChatTerm` integrates a TUI with a managed tmux session, providing instantaneous access to a ChatGPT client. Type `chat` to resume a session and copy the response to your clipboard at a keystroke; ChatTerm provides frictionless ChatGPT integration into your terminal-based workflow.

# Installation
Requires python 3.5+, `tmux`, and an `OPENAI_API_KEY`

```bash
git clone https://github.com/tcrensink/chat_term.git
cd chat_term
python install.py
```

# Usage
Type `chat` after installation and a new terminal session. This instantly connects to an existing `chat_term` session (or creates a new one as needed).

Terminal Commands:
```bash
chat # reconnect to existing or start new chat_term session
chat restart # force restarts chat_term session (when source is changed or error occurs)
chat stop # kills tmux chat_term session
chat --help # displays commands as described above
```

[Demo](https://user-images.githubusercontent.com/26497809/238851240-20f6f849-27f6-4e35-b6ef-e8ec761e63de.mov)
