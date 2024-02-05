# ChatTerm
A ChatGPT terminal client focused on easy access. Just type `chat`:


https://github.com/tcrensink/chat_term/assets/26497809/f4a1603d-3daa-4e00-8869-e972b74192f3



https://github.com/tcrensink/chat_term/assets/26497809/c981b090-61f3-4162-855e-6b80d93e8119






# Usage
**app commands**
```
ctrl+P: submit text
ctrl+O: expand text area
ctrl+R: reset chat session
ctrl+L: focus cursor on text area
ctrl+X: detach; return to terminal session
```

**terminal commands**
```bash
chat # resume/create chat_term session
chat restart # restart new chat_term session
chat stop # kill chat_term session
chat --help # displays commands as described above
```

# Installation

Requirements:
- python 3.9+
- tmux
- poetry
- openai api key

```bash
git clone https://github.com/tcrensink/chat_term.git
cd chat_term
python install.py
# open new shell session to use
```
