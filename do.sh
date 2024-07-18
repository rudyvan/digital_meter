#!/bin/bash
# use with sudo ./do.sh background or kill or run
kill_tasks() {
		for pid in $(ps -ef | awk '/launcher/ {print $2}'); do kill -9 $pid 1> /dev/null 2>&1; done
		for pid in $(ps -ef | awk '/digital_meter.py/ {print $2}'); do kill -9 $pid 1> /dev/null 2>&1; done
		for pid in $(ps -ef | awk '/tmux/ {print $2}'); do kill -9 $pid 1> /dev/null 2>&1; done
		for pid in $(ps -ef | awk '/do_panes/ {print $2}'); do kill -9 $pid 1> /dev/null 2>&1; done
}

WHAT=$1
case "$WHAT" in
	*kill*)
		#ps -o pid,sess,cmd afx   														# show all processes
		# kill "$(ps ax | awk '! /awk/ && /apps/ { print $1}')" 1> /dev/null 2>&1		# single process
		kill_tasks
	;;
	*start*)
		kill_tasks
		./launcher.sh &
	;;
	*run*)
		kill_tasks
		python3 digital_meter.py
	;;
	*upd*)
		kill_tasks
		cd dm_app
		git pull origin main
		cd ..
		python3 digital_meter.py
	;;
	*debug*)
		python3 digital_meter.py -d 1 &
	;;
  *bkup*)
    # make an image file, assume the usb disk is attached as sda
    HOSTNAME=$(cat /etc/hostname)
    cd /media
    mkdir sda
    echo $(lsblk )
    mount /dev/sda /media/sda
    echo "making $HOSTNAME.img takes a while.."
    dd if=/dev/mmcblk0 of=/media/sda/$HOSTNAME.img bs=1M
    unmount /media/sda
    echo "finished making $HOSTNAME.img and unmounted usb"
  ;;
	*)
		echo ""
		read -p "??use kill/start/run/usb/us4, press <enter> to continue"
esac

