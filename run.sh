#! /bin/bash

# manages tmux session for fast access
PROJECT_FOLDER="$(dirname "$0")"

# update as needed
TMUX_COMMAND="python $PROJECT_FOLDER/app.py"

# # handle starting/attaching to chat_term session (no arguments)
if [ $# -eq 0 ]; then
    if tmux has-session -t chat_term 2>/dev/null; then
        # session already exists, attach to it
        tmux attach-session -t chat_term
    else
    # if session does not exist, create it
        echo "starting chat_term session..."
        tmux -f "$PROJECT_FOLDER/tmux.conf" new-session -E -d -s chat_term
        tmux send-keys -t chat_term "$TMUX_COMMAND" C-m
        sleep 2
        tmux attach-session -t chat_term
    fi
    exit 0
fi

if [ "$1" = "--help" ]; then
    echo "chat            # starts or connects to chat_term session"
    echo "chat restart    # restarts chat_term session in case of error"
    echo "chat stop       # kills tmux chat_term session"

elif [ "$1" = "restart" ]; then
    "$PROJECT_FOLDER/restart.sh"

elif [ "$1" = "stop" ]; then
    "$PROJECT_FOLDER/stop.sh"
    if [ $? -eq 0 ]; then
        echo "killed chat_term session"
    else
        echo "no chat_term session found"
    fi

else
    echo "unknown argument: $1"
    echo "try 'chat --help' for more information"
fi
