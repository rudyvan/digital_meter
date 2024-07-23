#!/bin/bash

case "$(uname)" in
    *"Linux"*)
      # run tmux and run our script inside session luce
      OS=$(hostnamectl | grep "Operating System:")
      case "$OS" in
          *"Ubuntu"*)
            HOME_DIR="/home/rudyv/digital_meter"
            USER_NAME="rudyv"
            HOST_NAME=$(cat /etc/hostname)
          ;;
          *"Raspbian"* | *"Debian"*)
            HOME_DIR="/home/pi/digital_meter"
            USER_NAME="pi"
            HOST_NAME=$(cat /etc/hostname)
          ;;
          *)
            echo -e "$OS not supported"
            read -p "Press <enter> to continue"
          ;;
      esac
      ;;
    *"Darwin"*)
      HOME_DIR="/Users/rudyv/MyApps/digital_meter"
      USER_NAME="rudyv"
      HOST_NAME=$(hostname | cut -d '.' -f1)
    ;;
    *)
      echo -e "$OS not supported"
      read -p "Press <enter> to continue"
    ;;
esac
cd $HOME_DIR
while true; do
    .venv/bin/python -u digital_meter.py
    if [ $? -eq 1 ]; then
      echo -e "Crashed!! Email then sleep 15s\n"
      echo -e "launcher.sh => i crashed!!\n"
      sleep 15s   # wait for 15 seconds to allow the job to be killed or restart
      echo -e "Sleep Finished, retrying action!!"
    fi
done
