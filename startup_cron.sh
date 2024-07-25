#!/bin/bash
# run tmux and run our script inside session luce
case "$(uname)" in
    *"Linux"*)
      OS=$(hostnamectl | grep "Operating System:")
      case "$OS" in
          *"Ubuntu"*)
            HOME_DIR="/home/rudyv"
            HOST_NAME=$(cat /etc/hostname)
            APP_DIR=$HOME_DIR/digital_meter
            USER_NAME="rudyv"
            TMUX="/usr/bin/tmux"
          ;;
          *"Raspbian"* | *"Debian"*)
            HOME_DIR="/home/pi"
            HOST_NAME=$(cat /etc/hostname)
            APP_DIR=$HOME_DIR/digital_meter
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
      APP_DIR=$HOME_DIR/MyApps/digital_meter
      USER_NAME="rudyv"
      TMUX="/usr/local/bin/tmux"
    ;;
    *)
      echo -e "$OS not supported"
      read -p "Press <enter> to continue"
    ;;
esac
PATH=/usr/bin:$PATH
cd $HOME_DIR
source .bashrc
source .profile
cd $APP_DIR
$TMUX set-option -g default-shell /bin/bash
# Run  tmux and create new-session, detach all sessions
$TMUX kill-session -t dm
$TMUX new-session -ds dm
# set the default shell
# $TMUX set-option -g default-shell /bin/bash
# run bash to save output
$TMUX send-keys -t dm "exec bash" C-m
# run do_dm.sh inside tmux window
$TMUX send-keys -t dm "./do_dm.sh" C-m
