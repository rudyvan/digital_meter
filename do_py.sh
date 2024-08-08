#!/bin/bash
if [ -z "$1" ]; then
  echo "missing <script.py>"
  exit
fi
if [[ $(uname) == *"Darwin"* ]]; then
  APP_DIR=$(echo ~)/MyApps/digital_meter
else
  APP_DIR=$(echo ~)/digital_meter
fi
cd $APP_DIR
sudo /bin/bash -c "source .venv/bin/activate"
source .venv/bin/activate
while true; do
    python -u $1
    if [ $? -eq 1 ]; then
      echo -e "Crashed!! -> sleep 15s\n"
      echo -e "do_py.sh => i crashed!!\n"
      sleep 15
      echo -e "Sleep Finished, retrying action!!"
    fi
done
