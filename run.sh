#! /bin/bash

# manages tmux session for fast access
PROJECT_FOLDER="$(dirname "$0")"

# update as needed
TMUX_COMMAND="cd $PROJECT_FOLDER && clear && echo 'starting chat term... ' && uv run app.py"

# # handle starting/attaching to chat_term session (no arguments)
if [ $# -eq 0 ]; then
    if tmux has-session -t chat_term 2>/dev/null; then
        # session already exists, attach to it
        tmux attach-session -t chat_term
    else
    # if session does not exist, create it
        echo "starting chat_term session..."
        tmux -f "$PROJECT_FOLDER/tmux.conf" new-session -d -s chat_term
        tmux send-keys -t chat_term "$TMUX_COMMAND" C-m
        tmux attach-session -t chat_term
    fi
    exit 0
fi

if [ "$1" = "--help" ]; then
    echo "chat            # starts or connects to chat_term session"
    echo "chat restart    # restarts chat_term session in case of error"
    echo "chat stop       # kills tmux chat_term session"
    echo "chat ls         # list tmux sessions"
    echo "chat update     # update to latest version"
    echo "chat config     # show paths to config and secret files"

elif [ "$1" = "restart" ]; then
    tmux kill-session -t chat_term
    "$PROJECT_FOLDER/run.sh"
elif [ "$1" = "ls" ]; then
    output=$(tmux ls | grep chat_term)
    if [ -z "$output" ]; then
        echo "no chat_term session found"
    else
        echo "$output"
    fi
elif [ "$1" = "stop" ]; then
    tmux kill-session -t chat_term
    if [ $? -eq 0 ]; then
        echo "killed chat_term session"
    else
        echo "no chat_term session found"
    fi
elif [ "$1" = "update" ]; then
    tmux kill-session -t chat_term
    echo "updating from lock file..."
    cd "$PROJECT_FOLDER" && git checkout master && git pull
    uv sync
    echo "Update complete. You can restart chat_term now"

elif [ "$1" = "config" ]; then
    echo "$PROJECT_FOLDER/config.json"
    echo "$PROJECT_FOLDER/secrets.json"

else
    echo "unknown argument: $1"
    echo "available options:"
    echo "chat            # starts or connects to chat_term session"
    echo "chat restart    # restarts chat_term session in case of error"
    echo "chat stop       # kills tmux chat_term session"
    echo "chat ls         # list tmux sessions"
    echo "chat update     # update to latest version"
    echo "chat config     # show paths to config and secret files"
fi
