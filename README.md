# Simple speech-to-text (STT) and LLM text-to-speech (TTS) Utility
-----
### A simple voice interface to a local LLM. Activate the mic by pressing `fn + F2` and speak your prompt (upto 5 seconds).

`start_assistant.sh`
Edit this bash file before running it with `sh ./start_assistant.sh`. Check the path and python environment match your own.

`key_trigger.py`
The background service that lsitens for the F2 key press. Nothing to edit in here.

`qwen_voice.1.1.py`
The background service that performs the STT, TSS, and LLM exchange. Edit your paths in `main()` 

`com.user.qwenassistant.plist`
Config for the lunchctl service. Edit the paths.

# Stack

* oMLX
* Qwen2.5-Coder-7B-Instruct-MLX-8bit
* Qwen3-ASR-0.6B-8bit
* Qwen3-ASR-0.6B-8bit

## Setup

Run `sh ./start_assistant.sh` to setup everything.

The service will launch at boot but manually start it like this 

    `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.qwenassistant.plist`

Stop the service like this

    `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.user.qwenassistant.plist`

Watch the interaction log files like this 

    `tail -f /Users/admin/Developer/stt-tts-qwen/assistant_output.log`



Note: Since key_trigger.py relies on pynput to listen for the global F2 event, make sure your background daemon system manager has structural Accessibility privileges if macOS prompts you. If it doesn't fire at first, toggling your terminal app or launchd entries inside System Settings > Privacy & Security > Accessibility resolves the system lock