#!/bin/bash
# Script to setup Shift+Super+S shortcut for LinSnipper
# Supports: GNOME, Cinnamon

NAME="LinSnipper Snip"
CMD="linsnipper --snip"
BINDING="<Shift><Super>s"

# Detect DE
echo "Detecting Desktop Environment..."
if [ "$XDG_CURRENT_DESKTOP" = "" ]; then
  DESKTOP=$DESKTOP_SESSION
else
  DESKTOP=$XDG_CURRENT_DESKTOP
fi
echo "Environment: $DESKTOP"

configure_gnome() {
    echo "Configuring for GNOME..."
    PATH_CUSTOM="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"
    SCHEMA="org.gnome.settings-daemon.plugins.media-keys"
    
    # Generate ID
    ID="custom$(date +%s)"
    KEY_PATH="$PATH_CUSTOM/$ID/"

    EXISTING_LIST=$(gsettings get $SCHEMA custom-keybindings)
    if [[ "$EXISTING_LIST" == "@as []" ]]; then
        NEW_LIST="['$KEY_PATH']"
    else
        NEW_LIST="${EXISTING_LIST%]}, '$KEY_PATH']"
    fi

    gsettings set $SCHEMA custom-keybindings "$NEW_LIST"
    gsettings set $SCHEMA.custom-keybinding:$KEY_PATH name "$NAME"
    gsettings set $SCHEMA.custom-keybinding:$KEY_PATH command "$CMD"
    gsettings set $SCHEMA.custom-keybinding:$KEY_PATH binding "$BINDING"
}

configure_cinnamon() {
    echo "Configuring for Cinnamon..."
    base_schema="org.cinnamon.desktop.keybindings"
    custom_list_key="custom-list"
    
    # 1. Get current list of custom keybindings (e.g. ['custom0', 'custom1'])
    # Cinnamon stores a list of STRINGS (names of sub-schemas), not full paths.
    current_list=$(gsettings get $base_schema $custom_list_key)
    
    # Create new ID (customX)
    # Parse existing to find next index or just append timestamp to be safe
    # Cinnamon usually expects "custom0", "custom1". Let's try to find a free slot or use timestamp.
    # Actually Cinnamon is flexible. Let's use 'custom_linsnipper'
    
    new_id="custom_linsnipper"
    
    if [[ "$current_list" == *"'$new_id'"* ]]; then
        echo "Shortcut entry already exists. Updating..."
    else
        if [[ "$current_list" == "@as []" ]]; then
            new_list="['$new_id']"
        else
            new_list="${current_list%]}, '$new_id']"
        fi
        gsettings set $base_schema $custom_list_key "$new_list"
    fi
    
    # 2. Set properties
    # Schema: org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom_linsnipper/
    path="/org/cinnamon/desktop/keybindings/custom-keybindings/$new_id/"
    
    gsettings set $base_schema.custom-keybinding:$path name "$NAME"
    gsettings set $base_schema.custom-keybinding:$path command "$CMD"
    gsettings set $base_schema.custom-keybinding:$path binding_list "['$BINDING']" # Cinnamon uses list for bindings
    
    echo "Cinnamon configuration complete."
}

if [[ "$DESKTOP" == *"Cinnamon"* ]]; then
    configure_cinnamon
elif [[ "$DESKTOP" == *"GNOME"* ]]; then
    configure_gnome
else
    echo "Warning: Unsupported or unknown Desktop Environment: $DESKTOP"
    echo "Attempting GNOME configuration as fallback..."
    configure_gnome
fi

echo "Done! Press $BINDING to test."
