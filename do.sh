#!/bin/bash
# use with sudo ./do.sh background or kill or run
kill_tasks() {
		for pid in $(ps -ef | awk '/do_py/ {print $2}'); do kill -9 $pid 1> /dev/null 2>&1; done
		for pid in $(ps -ef | awk '/dm.py/ {print $2}'); do kill -9 $pid 1> /dev/null 2>&1; done
}

WHAT=$1
case "$WHAT" in
	*kill*)
		kill_tasks
	;;
	*start*)
		kill_tasks
		./do_py.sh dm.py &
	;;
	*run*)
		kill_tasks
		python dm.py
	;;
	*upd*)
		kill_tasks
		git pull origin main
		./do_py.sh dm.py &
	;;
	*)
		echo ""
		read -p "??use kill/start/run/upd, press <enter> to continue"
esac
$(exit 0)

