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
error_exit() {
    LOG=$HOST_NAME"_err.log"
    echo "$LOG"
    touch $LOG
    echo -e "Crashed!! Email then sleep 15s\n" 
    echo -e "launcher.sh => i crashed!! Email then sleep 15s\n" >>$LOG
    echo -e "see err file" | mail -s "$HOST_NAME Crashed!!!!" rudy_vandenberghe@hotmail.com
    sleep 15s   # wait for 15 seconds to allow the job to be killed or restart
    echo -e "Sleep Finished, retrying action!!"
    echo -e "launcher.sh => Sleep Finished, retrying action!!\n" >>$LOG
}
echo -e "sleep 10 seconds to catch /dev/tty1 when it is free"
sleep 10s
OUT="/dev/tty1" # define out
source .venv/bin/activate
while true; do
    echo -e "Now Running $HOST_NAME" | sudo tee $OUT
    python3 -u digital_meter.py | sudo tee $OUT
    if [ $? -eq 1 ]; then
        error_exit
    fi
done
