#!/bin/bash

cd /home/pi/iot49

# activate virtual environment from script
eval "$(direnv export bash)"

python /home/pi/iot49/projects/robot/code-pi/shutdown_monitor.py
