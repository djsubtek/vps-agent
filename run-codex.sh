#!/bin/bash

SESSION="codex"

# prüfen ob tmux installiert ist
if ! command -v tmux &> /dev/null
then
    echo "tmux ist nicht installiert. Installiere es mit:"
    echo "sudo apt install tmux"
    exit 1
fi

# prüfen ob session existiert
tmux has-session -t $SESSION 2>/dev/null

if [ $? != 0 ]; then
    echo "Starte neue Codex tmux Session..."
    tmux new-session -d -s $SESSION "cd /opt/vps-agent && scripts/openclaw-task.sh -- codex"
else
    echo "Codex Session läuft bereits."
fi

# attach
tmux attach -t $SESSION
