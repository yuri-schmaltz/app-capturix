#!/usr/bin/env python3
"""
Investigation script for Real Window Capture on X11.
Requires: python-xlib, ewmh (pip install python-xlib ewmh)

Goal: List regular windows and their geometry to see if we can capture them specifically.
"""

import sys

try:
    from ewmh import EWMH
    from Xlib import X, display
except ImportError:
    print("MISSING DEPENDENCIES: Please run 'pip install python-xlib ewmh'")
    sys.exit(1)

def main():
    try:
        ewmh = EWMH()
    except Exception as e:
        print(f"FAILED to connect to X Server (maybe Wayland?): {e}")
        sys.exit(1)

    print("Connected to X Server via EWMH.")
    print("-" * 40)

    wins = ewmh.getClientList()
    print(f"Total windows found: {len(wins)}")

    for win in wins:
        try:
            name = ewmh.getWmName(win)
            if not name:
                name = "<Unknown>"
            
            # Filter out panels/docks usually
            # types = ewmh.getWmWindowType(win)
            
            geo = win.get_geometry()
            pid = ewmh.getWmPid(win)
            
            # Check for visibility/mapping state if possible
            attrs = win.get_attributes()
            is_viewable = (attrs.map_state == X.IsViewable)
            
            if is_viewable:
                print(f"[ID: {win.id}] '{name}'")
                print(f"    PID: {pid}")
                print(f"    Geometry: {geo.x},{geo.y} {geo.width}x{geo.height}")
                print(f"    Root: {geo.root.id}")
        except Exception as e:
            print(f"    Error reading window {win.id}: {e}")

if __name__ == "__main__":
    main()
