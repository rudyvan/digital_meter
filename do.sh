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
		python3 lucy.py
	;;
	*upd*)
		kill_tasks
		cd lucy_app
		git pull origin main
		cd ..
		python3 lucy.py
	;;
	*debug*)
		python3 lucy.py -d 1 &
	;;
	*usb*)
		# unfortunately, sometimes the sms dongle seem to got lost from the usb bus and power need to be recycled.
		# unfortunately the network goes down too..
		# this script recycles the usb power and restores networking
		# https://www.raspberrypi.org/forums/viewtopic.php?t=32781
		usb_mem=`ls -d /sys/devices/platform/soc/*.usb`
		echo $usb_mem
		service networking stop
		sleep 5
		echo 0 > $usb_mem/buspower
		sleep 10
		echo 1 > $usb_mem/buspower
		sleep 5
		service networking start
	;;
	*us4*)
	  # install and compile https://github.com/codazoda/hub-ctrl.c
	  # see with sudo ./uhubctl/uhubctl (no args) where the sms system is and then construct/update this command
	  # assume the modem is plugged in port 1
		./uhubctl/uhubctl -l 1-1 -p 1 -a cycle
		./uhubctl/uhubctl -l 1-1 -p 2 -a off
		./uhubctl/uhubctl -l 1-1 -p 3 -a off
		./uhubctl/uhubctl -l 1-1 -p 4 -a off
		./uhubctl/uhubctl -l 1-1 -p 3 -a on
		./uhubctl/uhubctl -l 1-1 -p 2 -a on
		./uhubctl/uhubctl -l 1-1 -p 1 -a on
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

