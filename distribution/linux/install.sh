#!/bin/bash
set -e

# Scholarr Linux Installer
# Installs as a systemd service with SQLite (no database server needed)
# Install path: /opt/scholarr | Config: /etc/scholarr | Data: /var/lib/scholarr

VERSION="0.2.0"

echo ""
echo "  Scholarr v${VERSION} — Linux Installer"
echo "  ────────────────────────────────────"
echo ""

# Must be root
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: Run as root (sudo bash install.sh)"
    exit 1
fi

# Detect distro
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "ERROR: Cannot detect distribution"
    exit 1
fi
echo "  System: $OS $(uname -m)"

# Find or install Python 3.11+
PYTHON=""
for p in python3.12 python3.11 python3; do
    if command -v $p &>/dev/null; then
        ver=$($p -c 'import sys;print(sys.version_info.minor)')
        if [ "$ver" -ge 11 ]; then
            PYTHON=$(command -v $p)
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "  Installing Python..."
    case $OS in
        ubuntu|debian) apt-get update -qq && apt-get install -y -qq python3 python3-venv python3-pip ;;
        fedora|rhel|centos) dnf install -y -q python3 python3-pip ;;
        arch) pacman -S --noconfirm python python-pip ;;
        alpine) apk add --no-cache python3 py3-pip ;;
        *) echo "ERROR: Install Python 3.11+ manually"; exit 1 ;;
    esac
    PYTHON=$(command -v python3)
fi
echo "  Python: $($PYTHON --version)"

# Create user
if ! id scholarr &>/dev/null; then
    useradd -r -s /bin/false -d /var/lib/scholarr -m scholarr
fi

# Directories
mkdir -p /opt/scholarr /etc/scholarr /var/lib/scholarr/{data,backups,uploads}
chown -R scholarr:scholarr /var/lib/scholarr

# Virtual environment
echo "  Creating virtual environment..."
$PYTHON -m venv /opt/scholarr/venv
source /opt/scholarr/venv/bin/activate
pip install --upgrade pip -q

# Install
echo "  Installing Scholarr..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
if [ -f "$REPO_ROOT/pyproject.toml" ]; then
    pip install -e "$REPO_ROOT" -q
else
    pip install scholarr -q
fi

# Generate config
API_KEY=$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')
cat > /etc/scholarr/scholarr.env << EOF
# Scholarr Configuration (generated $(date +%Y-%m-%d))
SCHOLARR_API_KEY=${API_KEY}
SCHOLARR_DATABASE_URL=sqlite+aiosqlite:///var/lib/scholarr/data/scholarr.db
SCHOLARR_DATA_DIR=/var/lib/scholarr/data
SCHOLARR_UPLOAD_DIR=/var/lib/scholarr/uploads
SCHOLARR_BACKUP_DIR=/var/lib/scholarr/backups
SCHOLARR_LOG_LEVEL=info
SCHOLARR_PORT=8787
EOF
chmod 600 /etc/scholarr/scholarr.env
chown scholarr:scholarr /etc/scholarr/scholarr.env

# Systemd service
cat > /etc/systemd/system/scholarr.service << EOF
[Unit]
Description=Scholarr Academic Manager
After=network.target

[Service]
Type=simple
User=scholarr
Group=scholarr
EnvironmentFile=/etc/scholarr/scholarr.env
WorkingDirectory=/var/lib/scholarr
ExecStart=/opt/scholarr/venv/bin/uvicorn scholarr.app:create_app --factory --host 0.0.0.0 --port 8787
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable scholarr

echo ""
echo "  Installation complete!"
echo ""
echo "  API Key: ${API_KEY}"
echo "  Config:  /etc/scholarr/scholarr.env"
echo "  Data:    /var/lib/scholarr/"
echo ""
echo "  Start:   sudo systemctl start scholarr"
echo "  Status:  sudo systemctl status scholarr"
echo "  Logs:    journalctl -u scholarr -f"
echo "  Open:    http://localhost:8787"
echo ""
