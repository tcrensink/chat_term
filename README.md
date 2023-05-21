# ChatTerm
The fastest terminal access to ChatGPT.

`ChatTerm` integrates a TUI with a tmux session, providing instantaneous access to a ChatGPT client. Type `chat` to resume a session, copy the response to your clipboard at a keystroke; its a frictionless integration into your daily (terminal-based) workflow.

# Installation
Requires python 3.5+, `tmux`, and an `OPENAI_API_KEY`

```bash
git clone https://github.com/tcrensink/chat_term.git
cd chat_term
python install.py
```

# Usage
After install (and a new shell session) type `chat` to connect to the TUI. Reconnecting to a session is instantaneous.

[Demo](https://user-images.githubusercontent.com/26497809/238851240-20f6f849-27f6-4e35-b6ef-e8ec761e63de.mov)
