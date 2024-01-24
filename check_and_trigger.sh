#!/bin/bash

# Marker path
MARKER_PATH="/Users/shanto/LFL/lab_manager/markers/marker_$(date +%Y-%m-%d).txt"

# Check if the marker file exists for the current day
if [ ! -f "$MARKER_PATH" ]; then
    # Marker file doesn't exist - run trigger.sh
    /Users/shanto/LFL/lab_manager/trigger.sh
fi

