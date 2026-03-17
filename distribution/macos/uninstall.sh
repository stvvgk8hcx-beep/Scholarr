#!/bin/bash
echo "Uninstalling Scholarr..."
launchctl unload ~/Library/LaunchAgents/com.scholarr.agent.plist 2>/dev/null || true
rm -f ~/Library/LaunchAgents/com.scholarr.agent.plist
sudo rm -rf /usr/local/opt/scholarr
sudo rm -f /usr/local/bin/scholarr
echo "Scholarr uninstalled. Data preserved at ~/.local/share/scholarr/"
echo "To remove data: rm -rf ~/.local/share/scholarr ~/.config/scholarr"
