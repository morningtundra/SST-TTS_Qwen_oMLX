#!/usr/bin/env python
import socket
import sys

try:
    from pynput import keyboard
except ImportError:
    print("Install pynput for this script: pip install pynput")
    sys.exit(1)

# Network Configuration (Must match qwen_voice.1.1.py)
UDP_IP = "127.0.0.1"
UDP_PORT = 9999

def send_trigger():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(b"TRIGGER", (UDP_IP, UDP_PORT))
        sock.close()
        print(" -> Trigger packet dispatched successfully.")
    except Exception as e:
        print(f" -> Failed to emit trigger: {e}")

def on_press(key):
    try:
        # Check specifically for the F2 key
        if key == keyboard.Key.f2:
            print("\n[F2 Pressed] Emitting trigger...")
            send_trigger()
    except Exception as e:
        print(f"Error handling keypress: {e}")

def main():
    print("Native Key Monitor Active. Listening for [F2]...")
    print("Press Ctrl+C in this terminal window to stop monitoring.")
    
    # Start the native macOS event listener loop
    with keyboard.Listener(on_press=on_press) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            print("\nKey monitor shutting down.")

if __name__ == "__main__":
    main()