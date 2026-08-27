#!/bin/bash
# Free Claude Code - Docker Deployment Script
# This script automates deployment to a Linux server
# Usage: bash scripts/deploy.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="free-claude-code"
REPO_URL="https://github.com/Alishahryar1/free-claude-code.git"
DEPLOY_DIR="/opt/free-claude-code"
ENV_FILE="$DEPLOY_DIR/.env"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
    fi
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

install_docker() {
    log_info "Installing Docker..."

    if check_command docker; then
        log_info "Docker is already installed"
        return
    fi

    # Install dependencies
    apt-get update
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # Add Docker repository
    echo \
        "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Start Docker
    systemctl start docker
    systemctl enable docker

    log_info "Docker installed successfully"
}

install_nginx() {
    read -p "Install Nginx for reverse proxy? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Skipping Nginx installation"
        return
    fi

    log_info "Installing Nginx..."

    if check_command nginx; then
        log_info "Nginx is already installed"
        return
    fi

    apt-get update
    apt-get install -y nginx

    systemctl start nginx
    systemctl enable nginx

    log_info "Nginx installed successfully"
    log_info "Copy nginx.conf.example to /etc/nginx/sites-available/fcc-server"
    log_info "Then run: systemctl restart nginx"
}

clone_repository() {
    log_info "Cloning repository..."

    if [ -d "$DEPLOY_DIR" ]; then
        log_warn "Directory $DEPLOY_DIR already exists"
        read -p "Update existing installation? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
        cd "$DEPLOY_DIR"
        git pull origin main
    else
        mkdir -p "$DEPLOY_DIR"
        git clone "$REPO_URL" "$DEPLOY_DIR"
        cd "$DEPLOY_DIR"
    fi

    log_info "Repository cloned/updated successfully"
}

configure_environment() {
    log_info "Setting up environment configuration..."

    if [ -f "$ENV_FILE" ]; then
        log_warn "Configuration file $ENV_FILE already exists"
        read -p "Edit configuration? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi

    # Copy example if doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        cp .env.example "$ENV_FILE"
        chmod 600 "$ENV_FILE"
        log_info "Created $ENV_FILE from .env.example"
    fi

    # Prompt for critical configuration
    read -p "Enter NVIDIA NIM API key (leave empty to skip): " NVIDIA_KEY
    if [ -n "$NVIDIA_KEY" ]; then
        sed -i "s/^# NVIDIA_NIM_API_KEY=.*/NVIDIA_NIM_API_KEY=$NVIDIA_KEY/" "$ENV_FILE"
    fi

    read -p "Enter OpenRouter API key (leave empty to skip): " OPENROUTER_KEY
    if [ -n "$OPENROUTER_KEY" ]; then
        sed -i "s/^# OPENROUTER_API_KEY=.*/OPENROUTER_API_KEY=$OPENROUTER_KEY/" "$ENV_FILE"
    fi

    log_info "Configuration saved to $ENV_FILE"
    log_warn "Please review and complete $ENV_FILE with all your API keys"
}

build_and_start() {
    log_info "Building Docker image and starting service..."

    cd "$DEPLOY_DIR"

    # Build image
    docker build -t free-claude-code:latest .

    # Start with docker-compose
    docker-compose up -d

    log_info "Service started successfully"
}

verify_installation() {
    log_info "Verifying installation..."

    sleep 3

    if docker-compose ps | grep -q "fcc-server"; then
        log_info "✓ Container is running"
    else
        log_error "Container failed to start"
    fi

    # Check health
    if curl -s http://localhost:8000/health > /dev/null; then
        log_info "✓ Server is healthy"
    else
        log_warn "⚠ Health check failed - server may still be starting"
    fi
}

print_summary() {
    log_info "Installation complete!"
    echo ""
    echo "================================"
    echo "  Free Claude Code Deployment"
    echo "================================"
    echo ""
    echo "Configuration file: $ENV_FILE"
    echo "Deployment directory: $DEPLOY_DIR"
    echo ""
    echo "Access the Admin UI at: http://localhost:8000"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    docker-compose -f $DEPLOY_DIR/docker-compose.yml logs -f"
    echo "  Stop service: docker-compose -f $DEPLOY_DIR/docker-compose.yml down"
    echo "  Restart:      docker-compose -f $DEPLOY_DIR/docker-compose.yml restart"
    echo ""
    echo "For remote access, configure Nginx as a reverse proxy."
    echo "See nginx.conf.example for reference."
    echo ""
}

# Main execution
main() {
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║  Free Claude Code - Docker Deployment  ║"
    echo "╚════════════════════════════════════════╝"
    echo ""

    check_root
    install_docker
    install_nginx
    clone_repository
    configure_environment
    build_and_start
    verify_installation
    print_summary
}

# Run main function
main "$@"
