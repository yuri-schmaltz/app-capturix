#!/bin/bash
# Script to setup Shift+Super+S shortcut on GNOME
# Launches: linsnipper --snip

NAME="LinSnipper Snip"
CMD="linsnipper --snip"
BINDING="<Shift><Super>s"
PATH_CUSTOM="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"

# Generate a unique ID for the keybinding
ID="custom$(date +%s)"
KEY_PATH="$PATH_CUSTOM/$ID/"

echo "Setting up GNOME shortcut..."
echo "Command: $CMD"
echo "Binding: $BINDING"

# 1. Add the new keybinding path to the list of custom keybindings
EXISTING_LIST=$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings)

if [[ "$EXISTING_LIST" == "@as []" ]]; then
    NEW_LIST="['$KEY_PATH']"
else
    # Remove closing bracket, add new path, close bracket
    NEW_LIST="${EXISTING_LIST%]}, '$KEY_PATH']"
fi

gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "$NEW_LIST"

# 2. Configure the keybinding properties
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEY_PATH name "$NAME"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEY_PATH command "$CMD"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KEY_PATH binding "$BINDING"

echo "Done! Press Shift+Super+S to test."
