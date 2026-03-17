#!/bin/bash
set -e

# Scholarr Linux Installer Script
# Installation path: /opt/scholarr
# Config path: /etc/scholarr
# Data path: /home/scholarr

echo "========================================"
echo "Scholarr v0.1.0 - Linux Installer"
echo "========================================"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "ERROR: This installer must be run as root"
   exit 1
fi

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
else
    echo "ERROR: Could not detect Linux distribution"
    exit 1
fi

echo "Detected: $OS $VERSION"
echo ""

# Install Python 3.11+
echo "Checking Python installation..."
if ! command -v python3.11 &> /dev/null; then
    echo "Installing Python 3.11..."
    case $OS in
        ubuntu|debian)
            apt-get update
            apt-get install -y python3.11 python3.11-venv python3.11-dev
            ;;
        fedora|rhel|centos)
            dnf install -y python3.11 python3.11-devel
            ;;
        arch)
            pacman -S --noconfirm python
            ;;
        alpine)
            apk add --no-cache python3 py3-pip
            ;;
        *)
            echo "ERROR: Unsupported distribution. Please install Python 3.11+ manually."
            exit 1
            ;;
    esac
else
    echo "Python 3.11 already installed"
fi

# Create scholarr system user
echo "Creating scholarr system user..."
if ! id -u scholarr > /dev/null 2>&1; then
    useradd -r -s /bin/false -d /home/scholarr -m scholarr
    echo "Created scholarr user"
else
    echo "scholarr user already exists"
fi

# Install system dependencies (MySQL client)
echo "Installing system dependencies..."
case $OS in
    ubuntu|debian)
        apt-get install -y default-mysql-client curl
        ;;
    fedora|rhel|centos)
        dnf install -y mysql curl
        ;;
    arch)
        pacman -S --noconfirm mysql-clients curl
        ;;
    alpine)
        apk add --no-cache mysql-client curl
        ;;
esac

# Create installation directory
echo "Creating installation directory..."
mkdir -p /opt/scholarr
chown -R scholarr:scholarr /opt/scholarr

# Create virtualenv
echo "Creating Python virtual environment..."
python3.11 -m venv /opt/scholarr/venv
source /opt/scholarr/venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install Scholarr package
echo "Installing Scholarr..."
if [ -f "pyproject.toml" ]; then
    # Installing from source
    pip install -e .
else
    # Installing from PyPI
    pip install scholarr==0.1.0
fi

# Create config directory
echo "Creating configuration directories..."
mkdir -p /etc/scholarr
mkdir -p /home/scholarr/.config/scholarr
mkdir -p /home/scholarr/.local/share/scholarr/library
mkdir -p /home/scholarr/.local/share/scholarr/inbox
chown -R scholarr:scholarr /home/scholarr
chown -R scholarr:scholarr /etc/scholarr

# Create default environment file
echo "Creating environment configuration..."
RANDOM_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
cat > /etc/scholarr/scholarr.env << EOF
# Scholarr Environment Configuration
# Generated during installation: $(date)

# Application settings
SCHOLARR_ENVIRONMENT=production
SCHOLARR_LOG_LEVEL=info

# Database configuration - MySQL
# Update credentials and host as needed
SCHOLARR_DATABASE_URL=mysql+aiomysql://scholarr:scholarr_password@localhost:3306/scholarr

# API settings
SCHOLARR_SECRET_KEY=$RANDOM_SECRET
EOF
chmod 600 /etc/scholarr/scholarr.env
chown scholarr:scholarr /etc/scholarr/scholarr.env

# Install systemd service
echo "Installing systemd service..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/scholarr.service" ]; then
    cp "$SCRIPT_DIR/scholarr.service" /etc/systemd/system/scholarr.service
else
    echo "WARNING: scholarr.service not found in installer directory"
fi

# Reload systemd
systemctl daemon-reload

# Enable and start service
echo "Enabling Scholarr service..."
systemctl enable scholarr

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Set up MySQL database (or update credentials in: /etc/scholarr/scholarr.env)"
echo "2. Review configuration at: /etc/scholarr/scholarr.env"
echo "3. Start Scholarr with:"
echo "   systemctl start scholarr"
echo "4. Check status with:"
echo "   systemctl status scholarr"
echo "5. View logs with:"
echo "   journalctl -u scholarr -f"
echo ""
echo "Access Scholarr at: http://localhost:8787"
echo ""
