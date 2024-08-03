#!/bin/bash

case "$(uname)" in
    *"Linux"*)
      HOST_NAME=$(cat /etc/hostname)
      ;;
    *"Darwin"*)
      HOST_NAME=$(hostname | cut -d '.' -f1)
    ;;
    *)
      echo -e "$OS not supported"
    ;;
esac
HOME_DIR=$(echo ~)
APP_DIR=$HOME_DIR/digital_meter
cd $APP_DIR
sudo /bin/bash -c "source .venv/bin/activate"
source .venv/bin/activate
while true; do
    python -u $1
    if [ $? -eq 1 ]; then
      echo -e "Crashed!! Email then sleep 15s\n"
      echo -e "do_py.sh => i crashed!!\n"
      sleep 15s   # wait for 15 seconds to allow the job to be killed or restart
      echo -e "Sleep Finished, retrying action!!"
    fi
done
