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
# Run  tmux and create new-session, detach all sessions
$TMUX set-option -g default-shell /bin/bash
# create DM tmux session  (Digital Meter)
$TMUX kill-session -t dm
$TMUX new-session -ds dm
# run bash to save output
$TMUX send-keys -t dm "exec bash" C-m
# run do_py.sh inside tmux window
$TMUX send-keys -t dm "./do_py.sh dm.py" C-m
# create EV tmux session  (ELectric Vehicle)
$TMUX kill-session -t ev
$TMUX new-session -ds ev
# run bash to save output
$TMUX send-keys -t ev "exec bash" C-m
# run do_py.sh inside tmux window
$TMUX send-keys -t ev "./do_py.sh ev.py" C-m
# create BS tmux session  (Battery Storage)
$TMUX kill-session -t bs
$TMUX new-session -ds bs
# run bash to save output
$TMUX send-keys -t bs "exec bash" C-m
# run do_py.sh inside tmux window
$TMUX send-keys -t bs "./do_py.sh bs.py" C-m




