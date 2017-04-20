#!/bin/sh
# start-photobooth.sh
# navigate to home directory, then to this directory, then execute python script, then back home

# sleep for 3 seconds before starting again
sleep 10
cd /opt/photobooth
python3 photobooth.py