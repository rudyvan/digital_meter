#!/bin/bash
# run tmux and run our script inside session luce
case "$(uname)" in
    *"Linux"*)
      OS=$(hostnamectl | grep "Operating System:")
      case "$OS" in
          *"Ubuntu"*)
            HOME_DIR="/home/rudyv"
            APP_DIR=$HOME_DIR/lucy
            USER_NAME="rudyv"
            TMUX="/usr/bin/tmux"
          ;;
          *"Raspbian"* | *"Debian"*)
            HOME_DIR="/home/pi"
            APP_DIR=$HOME_DIR/lucy
            USER_NAME="pi"
            TMUX="/usr/bin/tmux"
          ;;
          *)
            echo -e "$OS not supported"
            read -p "Press <enter> to continue"
          ;;
      esac
      ;;
    *"Darwin"*)
      HOME_DIR="/Users/rudyv"
      APP_DIR=$HOME_DIR/MyApps/lucy
      USER_NAME="rudyv"
      TMUX="/usr/local/bin/tmux"
    ;;
    *)
      echo -e "$OS not supported"
      read -p "Press <enter> to continue"
    ;;
esac
# Run  tmux and create new-session, detach all sessions
$TMUX kill-session -t luce
$TMUX new-session -ds luce
# run python3 inside tmux window
$TMUX send-keys -t luce "cd $APP_DIR;python3.10 -u lucy.py" C-m
