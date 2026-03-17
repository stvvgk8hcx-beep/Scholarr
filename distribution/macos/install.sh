#!/bin/bash
set -e

# Scholarr macOS Installer
# Installs to /usr/local/opt/scholarr with LaunchAgent for auto-start
# Uses SQLite — no database server needed

VERSION="0.2.0"

echo ""
echo "  Scholarr v${VERSION} — macOS Installer"
echo "  ────────────────────────────────────"
echo ""

if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "ERROR: This installer is for macOS only"
    exit 1
fi

echo "  macOS $(sw_vers -productVersion)"

# Find Python 3.11+
PYTHON=""
for p in python3.12 python3.11 python3; do
    if command -v $p &>/dev/null; then
        ver=$($p -c 'import sys;print(sys.version_info.minor)' 2>/dev/null || echo "0")
        if [ "$ver" -ge 11 ]; then
            PYTHON=$(command -v $p)
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "  Python 3.11+ not found."
    if command -v brew &>/dev/null; then
        echo "  Installing via Homebrew..."
        brew install python@3.12
        PYTHON=$(brew --prefix python@3.12)/bin/python3.12
    else
        echo "  ERROR: Install Python 3.11+ from python.org or via Homebrew"
        exit 1
    fi
fi
echo "  Python: $($PYTHON --version)"

# Paths
INSTALL="/usr/local/opt/scholarr"
DATA="$HOME/.local/share/scholarr"
CONFIG="$HOME/.config/scholarr"

# Create dirs
echo "  Creating directories..."
sudo mkdir -p "$INSTALL"
sudo chown -R $(whoami) "$INSTALL"
mkdir -p "$DATA"/{data,uploads,backups} "$CONFIG"

# Venv
echo "  Creating virtual environment..."
$PYTHON -m venv "$INSTALL/venv"
source "$INSTALL/venv/bin/activate"
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

# Config
API_KEY=$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')
cat > "$CONFIG/scholarr.env" << EOF
SCHOLARR_API_KEY=${API_KEY}
SCHOLARR_DATABASE_URL=sqlite+aiosqlite:///${DATA}/data/scholarr.db
SCHOLARR_DATA_DIR=${DATA}/data
SCHOLARR_UPLOAD_DIR=${DATA}/uploads
SCHOLARR_BACKUP_DIR=${DATA}/backups
SCHOLARR_LOG_LEVEL=info
SCHOLARR_PORT=8787
EOF
chmod 600 "$CONFIG/scholarr.env"

# Launcher script
cat > "$INSTALL/run.sh" << EOF
#!/bin/bash
set -a; source "$CONFIG/scholarr.env"; set +a
exec "$INSTALL/venv/bin/uvicorn" scholarr.app:create_app --factory --host 127.0.0.1 --port 8787
EOF
chmod +x "$INSTALL/run.sh"
sudo ln -sf "$INSTALL/run.sh" /usr/local/bin/scholarr 2>/dev/null || true

# LaunchAgent
PLIST="$HOME/Library/LaunchAgents/com.scholarr.agent.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.scholarr.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>${INSTALL}/run.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${DATA}/scholarr.log</string>
    <key>StandardErrorPath</key>
    <string>${DATA}/scholarr.log</string>
</dict>
</plist>
EOF

echo ""
echo "  Installation complete!"
echo ""
echo "  API Key: ${API_KEY}"
echo "  Config:  ${CONFIG}/scholarr.env"
echo "  Data:    ${DATA}/"
echo ""
echo "  Start now:     scholarr"
echo "  Auto-start:    launchctl load ${PLIST}"
echo "  Stop:          launchctl unload ${PLIST}"
echo "  Open:          http://localhost:8787"
echo ""
