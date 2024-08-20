#!/bin/bash
HOME_DIR=$(echo ~)
cd $HOME_DIR
if [[ $(uname) == *"Darwin"* ]]; then
  APP_DIR=$HOME_DIR/MyApps/digital_meter
  BIN="/usr/local/bin"
  PATH=$BIN:$PATH
  # source .bash_profile
else
  APP_DIR=$HOME_DIR/digital_meter
  BIN="/usr/bin"
  PATH=$BIN:$PATH
  source .bashrc
  source .profile
fi
cd $APP_DIR
tmux set-option -g default-shell /bin/bash
tmux send-keys -t dm "exec bash" C-m
# run do_py.sh inside tmux window
tmux send-keys -t dm "./do_py.sh dm.py" C-m
# if you want to run the ev.py script as well, you can do it like this
tmux has-session -t ev 2>/dev/null
if [ $? != 0 ]; then
    tmux new-session -ds ev
fi
tmux send-keys -t ev "./do_py.sh ev.py" C-m
