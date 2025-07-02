#!/bin/sh

# This shell script will read the iSponsorBlockTV addon's logs and stream them to a pipe.
# This pipe should be read by an AppDaemon script that will look for lines containing
# the substring "Skipping segment: seeking to" then trigger an automation when found.
#
# Usage:
#   0. Store this script in /config/scripts/, and give it execute permissions.
#   1. Install the Advanced SSH & Web Terminal addon.
#   2. In the addon's configuration tab, add the following to init_commands:
#        nohup /config/scripts/sponsorblock_log_stream.sh &
#   3. Set up an AppDaemon script to read from the pipe (See: sponsorblock_monitor.py)

while true; do
    if [ ! -p /share/isponsorblock_log.pipe ]; then
        echo "Pipe not found. Creating named pipe: /share/isponsorblock_log.pipe"
        mkfifo /share/isponsorblock_log.pipe
    fi

    echo "Starting iSponsorBlockTV log stream..."
    /usr/bin/ha addons logs 932a64e5_isponsorblocktv -f > /share/isponsorblock_log.pipe

    echo "iSponsorBlockTV log stream connection closed. Restarting in 1 second..."
    sleep 1
done