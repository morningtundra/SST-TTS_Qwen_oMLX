# Simple speech-to-text (STT) and LLM text-to-speech (TTS) demo

Run `sh ./start_assistant.sh` to setup everything.

The service will launch at boot but manually start it like this 

`launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.qwenassistant.plist`

Stop the service like this

`launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.user.qwenassistant.plist`

Watch the log files like this 

`tail -f /Users/admin/Developer/stt-tts-qwen/assistant_output.log`

Note: Since key_trigger.py relies on pynput to listen for the global F2 event, make sure your background daemon system manager has structural Accessibility privileges if macOS prompts you. If it doesn't fire at first, toggling your terminal app or launchd entries inside System Settings > Privacy & Security > Accessibility resolves the system lock