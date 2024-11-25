#!/bin/bash

sudo apt-get update && apt-get upgrade -y
clear
sudo apt-get install -y curl wget screen jq  
clear
wget -O https://raw.githubusercontent.com/alkindivv/Natnode/refs/heads/main/loader.sh && chmod +x loader.sh && ./loader.sh
curl -s https://raw.githubusercontent.com/alkindivv/Natnode/refs/heads/main/logo.sh
sleep 4


# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

LOGFILE="install_log.txt"
exec > >(tee -a "$LOGFILE") 2>&1

# Function to display stylish messages
show() {
    echo -e "${CYAN}${BOLD}==> $1 ${NC}"
}

success() {
    echo -e "${GREEN}${BOLD}✔ $1 ${NC}"
}

warning() {
    echo -e "${YELLOW}${BOLD}⚠ $1 ${NC}"
}

error() {
    echo -e "${RED}${BOLD}✖ $1 ${NC}"
}

# Check for silent mode
SILENT=0
while getopts "s" opt; do
    case ${opt} in
        s ) SILENT=1 ;;
        \? ) echo "Usage: cmd [-s]"
             exit 1 ;;
    esac
done

if [ $SILENT -eq 1 ]; then
    AUTO_CONFIRM="-y"
else
    AUTO_CONFIRM=""
fi

# Verify the OS and version
OS=$(lsb_release -si)
VERSION=$(lsb_release -sr)

if [ "$OS" != "Ubuntu" ]; then
    error "This script only supports Ubuntu. Exiting..."
    exit 1
else
    show "Running on Ubuntu $VERSION"
fi

# Function to retry installations if they fail
retry_install() {
    PACKAGE=$1
    for i in {1..3}; do
        show "Installing $PACKAGE (attempt $i)..."
        sudo apt-get install -y $PACKAGE && success "$PACKAGE installed!" && break || warning "Retrying to install $PACKAGE ($i/3)..."
        if [ $i -eq 3 ]; then
            error "Failed to install $PACKAGE after 3 attempts. Exiting..."
            exit 1
        fi
    done
}

# Update and upgrade the system
# show "Updating system..."
# sudo apt update && sudo apt upgrade $AUTO_CONFIRM
# success "System updated and upgraded!"

# Function to install NVM (Node Version Manager)
check_node() {
    if ! command -v node &> /dev/null; then
        return 1
    fi
    return 0
}

if ! check_node; then
    echo "Node.js not found. Installing Node.js..."
    apt update && apt upgrade -y
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm install 22 && nvm alias default 22 && nvm use default
fi

# Install Docker if not installed
if ! command -v docker &> /dev/null; then
    show "Docker is not installed. Installing Docker version 27.1.1, build 63125853e3..."
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    retry_install docker-ce
    retry_install docker-ce-cli
    retry_install containerd.io

    # Add current user to docker group
    sudo usermod -aG docker $USER
    show "Please log out and log back in to use Docker without sudo."
else
    warning "Docker is already installed, skipping installation."
fi

# Final message

if ! command -v docker-compose &> /dev/null; then
    show "Installing the latest version of Docker Compose..."

    # Fetch the latest version of Docker Compose
    LATEST_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r .tag_name)

    # Download the latest version for Ubuntu x86_64
    sudo curl -L "https://github.com/docker/compose/releases/download/${LATEST_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

    # Apply execute permissions
    sudo chmod +x /usr/local/bin/docker-compose

    success "Docker Compose version ${LATEST_VERSION} installed successfully!"
else
    warning "Docker Compose is already installed, skipping installation."
fi

# Tambahkan verifikasi instalasi

echo "Verifying installations:"
echo "NVM version: $(nvm --version)"
echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"
echo "Docker version: $(docker --version)"
echo "Docker Compose version: $(docker-compose --version)"
show "All essential packages have been installed successfully!"
show "Visit my GitHub for more tutorials: https://github.com/alkindivv/Natnode."