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
