#!/usr/bin/env python3
"""Test arrow key detection"""

import sys
import tty
import termios
import threading
import time

def get_key():
    """Get a single keypress, handling arrow keys"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x1b':  # ESC sequence
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                ch3 = sys.stdin.read(1)
                if ch3 == 'A':
                    return 'UP'
                elif ch3 == 'B':
                    return 'DOWN'
                elif ch3 == 'C':
                    return 'RIGHT'
                elif ch3 == 'D':
                    return 'LEFT'
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def test_arrow_keys():
    """Test arrow key detection"""
    print("Arrow Key Test")
    print("Press arrow keys to test (or 'q' to quit)")
    print("=" * 40)
    
    while True:
        try:
            key = get_key()
            if key.lower() == 'q':
                print("Quitting...")
                break
            print(f"Key pressed: {key}")
        except KeyboardInterrupt:
            print("\nQuitting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    test_arrow_keys() 