#!/bin/bash
# run tmux and run our script inside session luce
case "$(uname)" in
    *"Linux"*)
      HOST_NAME=$(cat /etc/hostname)
      BIN="/usr/bin"
      ;;
    *"Darwin"*)
      HOST_NAME=$(hostname | cut -d '.' -f1)
      BIN="/usr/local/bin"
    ;;
    *)
      echo -e "$(uname) not supported"
      HOST_NAME=$(cat /etc/hostname)
      BIN="/usr/bin"
    ;;
esac
PATH=$BIN:$PATH
TMUX=$BIN/tmux
HOME_DIR=$(echo ~)
APP_DIR=$HOME_DIR/digital_meter
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




