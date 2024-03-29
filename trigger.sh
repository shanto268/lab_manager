#!/bin/bash
set -e

# notification function
notify() {
    GEN_NOTIFY_POVER="/Users/shanto/Programming/bin/generalNotification.py"
    PYTHON_EXE="/Users/shanto/anaconda3/bin/python"
    $PYTHON_EXE $GEN_NOTIFY_POVER "$1" "$2"
    tput bel
    local notification_command="display notification \"$2\" with title \"$1\""
    osascript -e "$notification_command"
}

# Source secrets
if [ -f "/Users/shanto/LFL/lab_manager/.secrets" ]; then
    source "/Users/shanto/LFL/lab_manager/.secrets"
else
    echo "Secrets file not found"
    exit 1
fi

# Activate conda environment
source /Users/shanto/anaconda3/etc/profile.d/conda.sh
conda activate lfl_tools

# Run the Python script and redirect output to a log file
DIR=/Users/shanto/LFL/lab_manager
# store the python binary path in a variable
PYTHON_BIN=/Users/shanto/anaconda3/envs/lfl_tools/bin/python
# store the path to the python script in a variable
PYTHON_SCRIPT=/Users/shanto/LFL/lab_manager/main.py
# store the path to the log file in a variable
LOG_FILE=/Users/shanto/LFL/lab_manager/cron.log
# change directory to the directory of the python script
cd $DIR
# Run the Python script and redirect output to a log file
{
    $PYTHON_BIN $PYTHON_SCRIPT >>$LOG_FILE 2>&1
} || true
EXIT_STATUS=$?

# Marker system implementation
MARKER_PATH="/Users/shanto/LFL/lab_manager/markers/marker_$(date +%Y-%m-%d).txt"
touch "$MARKER_PATH"

# Check if the script ran successfully
if [ $EXIT_STATUS -eq 0 ]; then
    notify "LFL Lab Manager" "Reminders and notifications sent."
elif [ $EXIT_STATUS -eq 1 ]; then
    notify "LFL Lab Manager" "Token expired or revoked."
else
    notify "LFL Lab Manager" "Script execution failed."
fi
