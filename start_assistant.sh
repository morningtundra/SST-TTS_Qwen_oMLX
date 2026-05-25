#!/bin/bash

# Navigate to the project directory
cd /Users/admin/Developer/stt-tts-qwen/

# Define the absolute path to your venv python binary
VENV_PYTHON="../.venv/bin/python"

# Install the required packages
pip install -r requirements.txt

# Create the launchctl service startup plist
cp com.user.qwenassistant.plist ~/Library/LaunchAgents/ 

# Handle graceful shutdown of both processes if the service stops
cleanup() {
    echo "Stopping local voice assistant services..."
    kill "$VOICE_PID" "$TRIGGER_PID" 2>/dev/null
    exit 0
}
trap cleanup SIGTERM SIGINT

echo "Starting isolated local voice engine..."
$VENV_PYTHON qwen_voice.1.1.py &
VOICE_PID=$!

echo "Starting native hotkey monitor..."
$VENV_PYTHON key_trigger.py &
TRIGGER_PID=$!

# Keep the wrapper alive and wait for the child processes
wait "$VOICE_PID" "$TRIGGER_PID"