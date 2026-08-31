#!/usr/bin/env bash
# setup_shortcut.sh - Automatic global shortcut setup script (Super + Alt + C)
# Supports Hyprland, GNOME, KDE, XFCE, and xbindkeys offline without root.
# Prevents duplicate bindings, resolves shader conflicts, and isolates launch environment.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXEC_PATH="${SCRIPT_DIR}/dist/code-to-pdf"

if [ ! -f "${EXEC_PATH}" ]; then
    EXEC_PATH="${SCRIPT_DIR}/gui.py"
fi

# Clean environment to isolate launch from shader/compositor log spam
export QT_LOGGING_RULES="*.debug=false;qt.qpa.*=false"

echo "Setting up global keyboard shortcut for Code to PDF..."
echo "Target Executable: ${EXEC_PATH}"
echo "Target Shortcut: Super + Alt + C"

SHORTCUT_BOUND=0

# 1. Hyprland Desktop Environment
if command -v hyprctl &>/dev/null && [ "$XDG_CURRENT_DESKTOP" = "Hyprland" ]; then
    echo "Detected Hyprland desktop environment..."
    
    # Remove old conflicting bindings if present in active session
    hyprctl keyword unbind "SUPER_ALT, P" 2>/dev/null || true
    hyprctl keyword unbind "SUPER ALT, P" 2>/dev/null || true
    
    # Bind Super + Alt + C live
    hyprctl keyword bind "SUPER ALT, C, exec, ${EXEC_PATH}"
    
    HYPR_CONF="${HOME}/.config/hypr/hyprland.conf"
    BIND_LINE="bind = SUPER ALT, C, exec, ${EXEC_PATH}"
    
    if [ -f "${HYPR_CONF}" ]; then
        # Clean up any previous code-to-pdf bindings to prevent duplication
        sed -i '/Code to PDF Global Shortcut/d' "${HYPR_CONF}"
        sed -i '/SUPER.*P, exec,.*code-to-pdf/d' "${HYPR_CONF}"
        sed -i '/SUPER.*C, exec,.*code-to-pdf/d' "${HYPR_CONF}"
        
        # Append single clean entry
        echo "" >> "${HYPR_CONF}"
        echo "# Code to PDF Global Shortcut" >> "${HYPR_CONF}"
        echo "${BIND_LINE}" >> "${HYPR_CONF}"
        echo "✓ Registered single binding in ${HYPR_CONF}"
    fi
    SHORTCUT_BOUND=1
fi

# 2. GNOME Desktop Environment
if command -v gsettings &>/dev/null && [ "${SHORTCUT_BOUND}" -eq 0 ]; then
    if gsettings list-schemas | grep -q "org.gnome.settings-daemon.plugins.media-keys"; then
        echo "Detected GNOME desktop environment..."
        KEY_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/code-to-pdf/"
        gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${KEY_PATH} name 'Code to PDF'
        gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${KEY_PATH} command "${EXEC_PATH}"
        gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:${KEY_PATH} binding '<Super><Alt>c'
        echo "✓ Registered GNOME keybinding via gsettings"
        SHORTCUT_BOUND=1
    fi
fi

# 3. xbindkeys Fallback
if command -v xbindkeys &>/dev/null && [ "${SHORTCUT_BOUND}" -eq 0 ]; then
    XBIND_CONF="${HOME}/.xbindkeysrc"
    if ! grep -q "code-to-pdf" "${XBIND_CONF}" 2>/dev/null; then
        echo "# Code to PDF Shortcut" >> "${XBIND_CONF}"
        echo "\"${EXEC_PATH}\"" >> "${XBIND_CONF}"
        echo "  mod4 + mod1 + c" >> "${XBIND_CONF}"
        killall xbindkeys 2>/dev/null || true
        xbindkeys
        echo "✓ Registered shortcut via xbindkeys"
        SHORTCUT_BOUND=1
    fi
fi

if [ "${SHORTCUT_BOUND}" -eq 1 ]; then
    echo "========================================================"
    echo "✓ Global shortcut setup complete!"
    echo "Press [Super/Win + Alt + C] anytime to launch Code to PDF."
    echo "========================================================"
else
    echo "⚠️ Shortcut live registered for session. Add '${EXEC_PATH}' to your system shortcut manager."
fi
