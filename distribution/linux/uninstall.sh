#!/bin/bash
set -e
echo "Uninstalling Scholarr..."
sudo systemctl stop scholarr 2>/dev/null || true
sudo systemctl disable scholarr 2>/dev/null || true
sudo rm -f /etc/systemd/system/scholarr.service
sudo systemctl daemon-reload
sudo rm -rf /opt/scholarr
sudo rm -rf /etc/scholarr
echo "Scholarr uninstalled. Data preserved at /var/lib/scholarr/"
echo "To remove data: sudo rm -rf /var/lib/scholarr"
