#!/bin/bash
# run tmux and run our script inside session luce
case "$(uname)" in
    *"Linux"*)
      OS=$(hostnamectl | grep "Operating System:")
      case "$OS" in
          *"Ubuntu"*)
            HOME_DIR="/home/rudyv"
            HOST_NAME=$(cat /etc/hostname)
            APP_DIR=$HOME_DIR/lucy
            USER_NAME="rudyv"
            TMUX="/usr/bin/tmux"
          ;;
          *"Raspbian"* | *"Debian"*)
            HOME_DIR="/home/pi"
            HOST_NAME=$(cat /etc/hostname)
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
      HOST_NAME=$(hostname | cut -d '.' -f1)
      APP_DIR=$HOME_DIR/MyApps/lucy
      USER_NAME="rudyv"
      TMUX="tmux"
    ;;
    *)
      echo -e "$OS not supported"
      read -p "Press <enter> to continue"
    ;;
esac
PATH=/usr/bin:$PATH
source $HOME_DIR/.bashrc
source $HOME_DIR/.profile
# Run  tmux and create new-session, detach all sessions
$TMUX kill-session -t luce
$TMUX new-session -ds luce
# set the default shell
$TMUX set-option -g default-shell /bin/bash
# run bash to save output
$TMUX send-keys -t luce "exec bash" C-m
# run launcher.sh inside tmux window
$TMUX send-keys -t luce "cd $APP_DIR;./launcher.sh" C-m
