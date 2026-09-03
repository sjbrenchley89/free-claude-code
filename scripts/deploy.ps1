# Free Claude Code - Docker Deployment Script (Windows PowerShell)
# This script automates deployment setup on Windows with Docker Desktop
# Usage: .\scripts\deploy.ps1

param(
    [switch]$SkipDocker = $false,
    [switch]$SkipNginx = $false
)

# Configuration
$ProjectName = "free-claude-code"
$RepoUrl = "https://github.com/Alishahryar1/free-claude-code.git"
$DeployDir = "C:\free-claude-code"
$EnvFile = Join-Path $DeployDir ".env"

# Functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    exit 1
}

function Test-CommandExists {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function Install-Docker {
    Write-Info "Checking Docker installation..."

    if (Test-CommandExists docker) {
        Write-Info "Docker is already installed"
        docker version
        return
    }

    Write-Warn "Docker is not installed"
    Write-Info "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    Write-Info "After installation, restart PowerShell and run this script again"
    exit 1
}

function Install-Git {
    Write-Info "Checking Git installation..."

    if (Test-CommandExists git) {
        Write-Info "Git is already installed"
        return
    }

    Write-Warn "Git is not installed"
    Write-Info "Please install Git from: https://git-scm.com/download/win"
    Write-Info "After installation, restart PowerShell and run this script again"
    exit 1
}

function Clone-Repository {
    Write-Info "Setting up repository..."

    if (Test-Path $DeployDir) {
        Write-Warn "Directory $DeployDir already exists"
        $response = Read-Host "Update existing installation? (y/n)"
        if ($response -ne "y") {
            return
        }
        cd $DeployDir
        git pull origin main
    }
    else {
        New-Item -ItemType Directory -Force -Path $DeployDir | Out-Null
        cd $DeployDir
        git clone $RepoUrl .
    }

    Write-Info "Repository ready at $DeployDir"
}

function Configure-Environment {
    Write-Info "Setting up environment configuration..."

    if (Test-Path $EnvFile) {
        Write-Warn "Configuration file $EnvFile already exists"
        $response = Read-Host "Edit configuration? (y/n)"
        if ($response -ne "y") {
            return
        }
    }

    # Copy example if doesn't exist
    if (-not (Test-Path $EnvFile)) {
        Copy-Item ".env.example" $EnvFile
        Write-Info "Created $EnvFile from .env.example"
    }

    Write-Info "Please edit $EnvFile with your API keys"
    Write-Info "Opening file editor..."
    & notepad $EnvFile
}

function Build-And-Start {
    Write-Info "Building Docker image and starting service..."

    cd $DeployDir

    # Build image
    Write-Info "Building Docker image..."
    docker build -t free-claude-code:latest .

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker build failed"
    }

    # Start with docker-compose
    Write-Info "Starting service with Docker Compose..."
    docker-compose up -d

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker Compose startup failed"
    }

    Write-Info "Service started successfully"
}

function Verify-Installation {
    Write-Info "Verifying installation..."

    Start-Sleep -Seconds 3

    $containerStatus = docker-compose ps | Select-String "fcc-server"
    if ($containerStatus) {
        Write-Info "✓ Container is running"
    }
    else {
        Write-Error "Container failed to start"
    }

    # Check health
    try {
        $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -ErrorAction SilentlyContinue
        if ($health.StatusCode -eq 200) {
            Write-Info "✓ Server is healthy"
        }
    }
    catch {
        Write-Warn "⚠ Health check failed - server may still be starting"
    }
}

function Print-Summary {
    Write-Info "Installation complete!"
    Write-Host ""
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "  Free Claude Code Deployment" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Configuration file: $EnvFile"
    Write-Host "Deployment directory: $DeployDir"
    Write-Host ""
    Write-Host "✓ Access the Admin UI at: http://localhost:8000"
    Write-Host ""
    Write-Host "Useful commands:"
    Write-Host "  View logs:    docker-compose logs -f"
    Write-Host "  Stop service: docker-compose down"
    Write-Host "  Restart:      docker-compose restart"
    Write-Host "  Status:       docker-compose ps"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Edit .env file with your API keys"
    Write-Host "  2. Restart the service: docker-compose restart"
    Write-Host "  3. Access Admin UI to verify configuration"
    Write-Host ""
}

# Main execution
function Main {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  Free Claude Code - Docker Deployment  ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    # Check prerequisites
    Install-Git
    Install-Docker

    # Main workflow
    Clone-Repository
    Configure-Environment
    Build-And-Start
    Verify-Installation
    Print-Summary

    Write-Host "✓ Deployment complete!" -ForegroundColor Green
}

# Run main function
Main
