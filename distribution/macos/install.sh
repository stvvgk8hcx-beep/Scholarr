#!/bin/bash
set -e

# Scholarr macOS Installer Script
# Installation path: /usr/local/opt/scholarr
# Config path: ~/.config/scholarr
# Data path: ~/.local/share/scholarr

echo "========================================"
echo "Scholarr v0.1.0 - macOS Installer"
echo "========================================"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "ERROR: This installer is for macOS only"
    exit 1
fi

echo "macOS $(sw_vers -productVersion) detected"
echo ""

# Check for Homebrew
echo "Checking Homebrew installation..."
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew found: $(brew --version | head -n1)"
fi

# Install Python 3.11+
echo ""
echo "Checking Python installation..."
if ! command -v python3.11 &> /dev/null; then
    echo "Installing Python 3.11..."
    brew install python@3.11
    brew link python@3.11 --force
else
    echo "Python 3.11 already installed"
fi

# Verify Python
PYTHON_PATH=$(which python3.11)
PYTHON_VERSION=$($PYTHON_PATH --version)
echo "Using: $PYTHON_PATH"
echo "Version: $PYTHON_VERSION"
echo ""

# Create installation directory
echo "Creating installation directory..."
INSTALL_PATH="/usr/local/opt/scholarr"
if [ ! -d "$INSTALL_PATH" ]; then
    sudo mkdir -p "$INSTALL_PATH"
    sudo chown -R $(whoami) "$INSTALL_PATH"
else
    echo "Installation directory already exists: $INSTALL_PATH"
fi

# Create data directories
echo "Creating data directories..."
mkdir -p ~/.config/scholarr
mkdir -p ~/.local/share/scholarr/{library,inbox,logs}

# Create virtual environment
echo "Creating Python virtual environment..."
$PYTHON_PATH -m venv "$INSTALL_PATH/venv"

# Activate virtualenv
source "$INSTALL_PATH/venv/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install Scholarr
echo "Installing Scholarr..."
if [ -f "pyproject.toml" ]; then
    # Installing from source
    pip install -e .
else
    # Installing from PyPI
    pip install scholarr==0.1.0
fi

# Create environment file
echo "Creating environment configuration..."
RANDOM_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
cat > ~/.config/scholarr/scholarr.env << EOF
# Scholarr Environment Configuration
# Generated during installation: $(date)

SCHOLARR_ENVIRONMENT=production
SCHOLARR_LOG_LEVEL=info
SCHOLARR_DATABASE_URL=mysql+aiomysql://scholarr:scholarr_password@localhost:3306/scholarr
SCHOLARR_SECRET_KEY=$RANDOM_SECRET
EOF
chmod 600 ~/.config/scholarr/scholarr.env

# Copy LaunchAgent plist
echo "Installing LaunchAgent..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LAUNCHAGENT_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCHAGENT_DIR"

if [ -f "$SCRIPT_DIR/com.scholarr.agent.plist" ]; then
    cp "$SCRIPT_DIR/com.scholarr.agent.plist" "$LAUNCHAGENT_DIR/com.scholarr.agent.plist"
    chmod 644 "$LAUNCHAGENT_DIR/com.scholarr.agent.plist"

    # Update paths in plist if necessary
    sed -i '' "s|\$HOME|$HOME|g" "$LAUNCHAGENT_DIR/com.scholarr.agent.plist"
else
    echo "WARNING: com.scholarr.agent.plist not found in installer directory"
fi

# Create convenience launcher script
echo "Creating launcher script..."
cat > "$INSTALL_PATH/scholarr" << 'LAUNCHER_EOF'
#!/bin/bash
source /usr/local/opt/scholarr/venv/bin/activate
exec uvicorn scholarr.app:app --host 0.0.0.0 --port 8787 --log-level info
LAUNCHER_EOF
chmod +x "$INSTALL_PATH/scholarr"

# Create symlink for easier access
echo "Creating symlink..."
sudo ln -sf "$INSTALL_PATH/scholarr" /usr/local/bin/scholarr 2>/dev/null || true

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Set up MySQL database (or update credentials in: ~/.config/scholarr/scholarr.env)"
echo "2. Review configuration at: ~/.config/scholarr/scholarr.env"
echo "3. Load the LaunchAgent:"
echo "   launchctl load ~/Library/LaunchAgents/com.scholarr.agent.plist"
echo "4. Scholarr will start automatically on next login"
echo "5. View logs with:"
echo "   tail -f ~/.local/share/scholarr/logs/scholarr.log"
echo ""
echo "Quick start:"
echo "  scholarr"
echo ""
echo "Access Scholarr at: http://localhost:8787"
echo ""
echo "To disable auto-start:"
echo "  launchctl unload ~/Library/LaunchAgents/com.scholarr.agent.plist"
echo ""
