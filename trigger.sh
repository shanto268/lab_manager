#!/bin/bash
set -e

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
# run the python script and redirect output to the log file
$PYTHON_BIN $PYTHON_SCRIPT >>$LOG_FILE 2>&1

# Marker system implementation
MARKER_PATH="/Users/shanto/LFL/lab_manager/markers/marker_$(date +%Y-%m-%d).txt"
touch "$MARKER_PATH"

