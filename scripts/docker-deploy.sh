#!/usr/bin/env bash
# Docker deployment setup and configuration script for free-claude-code
#
# Usage:
#   ./scripts/docker-deploy.sh setup      # Interactive setup
#   ./scripts/docker-deploy.sh build      # Build Docker image
#   ./scripts/docker-deploy.sh start      # Start with docker-compose
#   ./scripts/docker-deploy.sh stop       # Stop services
#   ./scripts/docker-deploy.sh test       # Run tests
#   ./scripts/docker-deploy.sh logs       # View logs
#   ./scripts/docker-deploy.sh help       # Show this help

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env.production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_dependencies() {
    print_header "Checking Dependencies"

    local missing=0

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        missing=$((missing + 1))
    else
        print_success "Docker $(docker --version)"
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        missing=$((missing + 1))
    else
        print_success "Docker Compose $(docker-compose --version)"
    fi

    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed"
        missing=$((missing + 1))
    else
        print_success "curl is installed"
    fi

    if [ $missing -gt 0 ]; then
        print_error "Please install missing dependencies"
        exit 1
    fi
}

setup_interactive() {
    print_header "Interactive Setup"

    echo "This script will help you configure free-claude-code for Docker deployment."
    echo ""

    # API Provider selection
    echo "Select your AI provider:"
    echo "  1) Anthropic Claude (Recommended for production)"
    echo "  2) Groq (Fastest, free tier)"
    echo "  3) OpenRouter (Multiple models)"
    echo "  4) DeepSeek (Cost-effective)"
    echo "  5) OpenAI (Requires ChatGPT subscription + OAuth setup)"
    echo "  6) Azure OpenAI (Enterprise)"
    read -p "Enter choice (1-6): " provider_choice

    case $provider_choice in
        1)
            print_info "You selected Anthropic Claude"
            setup_anthropic
            ;;
        2)
            print_info "You selected Groq"
            setup_groq
            ;;
        3)
            print_info "You selected OpenRouter"
            setup_openrouter
            ;;
        4)
            print_info "You selected DeepSeek"
            setup_deepseek
            ;;
        5)
            print_warning "OpenAI uses OAuth - will be configured in Admin UI after deployment"
            setup_openai
            ;;
        6)
            print_info "You selected Azure OpenAI"
            setup_azure_openai
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    # Optional: Enable authentication
    echo ""
    read -p "Enable API authentication? (y/n): " enable_auth
    if [[ $enable_auth == "y" ]]; then
        setup_authentication
    fi

    # Optional: Enable monitoring
    echo ""
    read -p "Enable Prometheus/Grafana monitoring? (y/n): " enable_monitoring
    if [[ $enable_monitoring == "y" ]]; then
        print_success "Monitoring will be available at http://localhost:9090 (Prometheus) and http://localhost:3000 (Grafana)"
    fi

    print_success "Configuration complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Build Docker image: ./scripts/docker-deploy.sh build"
    echo "  2. Start services: ./scripts/docker-deploy.sh start"
    echo "  3. Test the server: ./scripts/docker-deploy.sh test"
}

setup_anthropic() {
    echo ""
    echo "Anthropic Setup:"
    echo "  1. Visit: https://console.anthropic.com/account/keys"
    echo "  2. Create a new API key"
    echo "  3. Copy the key (starts with sk-ant-...)"
    echo ""
    read -sp "Enter your Anthropic API key: " api_key
    echo ""

    if [ -z "$api_key" ]; then
        print_error "API key cannot be empty"
        setup_anthropic
        return
    fi

    sed -i.bak "s/# ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$api_key/" "$ENV_FILE"

    # Set default model
    sed -i.bak "/ANTHROPIC_API_KEY=/a\\
FCC_DEFAULT_MODEL=anthropic/claude-3-5-sonnet-20241022" "$ENV_FILE"

    print_success "Anthropic configured"
    print_info "Default model: claude-3-5-sonnet-20241022"
}

setup_groq() {
    echo ""
    echo "Groq Setup:"
    echo "  1. Visit: https://console.groq.com/keys"
    echo "  2. Create a new API key"
    echo "  3. Copy the key"
    echo ""
    read -sp "Enter your Groq API key: " api_key
    echo ""

    if [ -z "$api_key" ]; then
        print_error "API key cannot be empty"
        setup_groq
        return
    fi

    sed -i.bak "s/# GROQ_API_KEY=.*/GROQ_API_KEY=$api_key/" "$ENV_FILE"
    sed -i.bak "/GROQ_API_KEY=/a\\
FCC_DEFAULT_MODEL=groq/llama-3.3-70b-versatile" "$ENV_FILE"

    print_success "Groq configured"
    print_info "Default model: llama-3.3-70b-versatile"
}

setup_openrouter() {
    echo ""
    echo "OpenRouter Setup:"
    echo "  1. Visit: https://openrouter.ai/keys"
    echo "  2. Create a new API key"
    echo "  3. Copy the key"
    echo ""
    read -sp "Enter your OpenRouter API key: " api_key
    echo ""

    if [ -z "$api_key" ]; then
        print_error "API key cannot be empty"
        setup_openrouter
        return
    fi

    sed -i.bak "s/# OPENROUTER_API_KEY=.*/OPENROUTER_API_KEY=$api_key/" "$ENV_FILE"
    sed -i.bak "/OPENROUTER_API_KEY=/a\\
FCC_DEFAULT_MODEL=openai/gpt-4-turbo" "$ENV_FILE"

    print_success "OpenRouter configured"
    print_info "Default model: gpt-4-turbo (access to OpenAI models via OpenRouter)"
}

setup_deepseek() {
    echo ""
    echo "DeepSeek Setup:"
    echo "  1. Visit: https://platform.deepseek.com/api_keys"
    echo "  2. Create a new API key"
    echo "  3. Copy the key"
    echo ""
    read -sp "Enter your DeepSeek API key: " api_key
    echo ""

    if [ -z "$api_key" ]; then
        print_error "API key cannot be empty"
        setup_deepseek
        return
    fi

    sed -i.bak "s/# DEEPSEEK_API_KEY=.*/DEEPSEEK_API_KEY=$api_key/" "$ENV_FILE"
    sed -i.bak "/DEEPSEEK_API_KEY=/a\\
FCC_DEFAULT_MODEL=deepseek/deepseek-chat" "$ENV_FILE"

    print_success "DeepSeek configured"
    print_info "Default model: deepseek-chat"
}

setup_openai() {
    echo ""
    echo "OpenAI Setup (OAuth):"
    echo "  Note: OpenAI uses OAuth authentication"
    echo "  After deploying, you'll configure it in the Admin UI:"
    echo ""
    echo "  1. Start the server: ./scripts/docker-deploy.sh start"
    echo "  2. Open: http://localhost:8082/admin"
    echo "  3. Go to 'Providers → Connected accounts'"
    echo "  4. Click 'Connect OpenAI'"
    echo "  5. Complete device code flow or browser OAuth"
    echo "  6. Restart the server"
    echo ""

    print_info "OpenAI provider will be configured after deployment"
}

setup_azure_openai() {
    echo ""
    echo "Azure OpenAI Setup:"
    echo "  1. Visit: https://portal.azure.com"
    echo "  2. Create an Azure OpenAI resource"
    echo "  3. Get API key and deployment name"
    echo ""
    read -sp "Enter your Azure OpenAI API key: " api_key
    echo ""
    read -p "Enter your Azure OpenAI base URL (https://your-resource.openai.azure.com): " base_url

    if [ -z "$api_key" ] || [ -z "$base_url" ]; then
        print_error "API key and base URL cannot be empty"
        setup_azure_openai
        return
    fi

    sed -i.bak "s|# AZURE_OPENAI_API_KEY=.*|AZURE_OPENAI_API_KEY=$api_key|" "$ENV_FILE"
    sed -i.bak "s|# AZURE_OPENAI_BASE_URL=.*|AZURE_OPENAI_BASE_URL=$base_url|" "$ENV_FILE"

    print_success "Azure OpenAI configured"
}

setup_authentication() {
    echo ""
    echo "API Authentication Setup:"

    # Generate a random token
    random_token=$(openssl rand -base64 32)

    read -p "Use generated token? (y/n): " use_generated
    if [[ $use_generated == "y" ]]; then
        auth_token=$random_token
    else
        read -sp "Enter your authentication token: " auth_token
        echo ""
    fi

    sed -i.bak "s/# PROXY_AUTH_ENABLED=.*/PROXY_AUTH_ENABLED=true/" "$ENV_FILE"
    sed -i.bak "s/# ANTHROPIC_AUTH_TOKEN=.*/ANTHROPIC_AUTH_TOKEN=$auth_token/" "$ENV_FILE"

    print_success "Authentication enabled"
    print_warning "Remember your token: $auth_token"
}

build_docker_image() {
    print_header "Building Docker Image"

    if [ ! -f "$PROJECT_ROOT/Dockerfile" ]; then
        print_error "Dockerfile not found in $PROJECT_ROOT"
        exit 1
    fi

    print_info "Building image: free-claude-code:latest"
    docker build -t free-claude-code:latest "$PROJECT_ROOT"

    print_success "Docker image built successfully"
}

start_services() {
    print_header "Starting Services"

    if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        print_error "docker-compose.yml not found"
        exit 1
    fi

    if [ ! -f "$ENV_FILE" ]; then
        print_error ".env.production not found"
        print_warning "Please run: ./scripts/docker-deploy.sh setup"
        exit 1
    fi

    print_info "Starting services with docker-compose..."
    cd "$PROJECT_ROOT"
    docker-compose up -d

    print_success "Services started"

    # Wait for server to be ready
    print_info "Waiting for server to be ready..."
    for i in {1..30}; do
        if curl -sf http://localhost:8082/health > /dev/null 2>&1; then
            print_success "Server is ready!"
            break
        fi
        echo -n "."
        sleep 1
    done

    echo ""
    echo ""
    echo "Access points:"
    echo "  API Server: http://localhost:8082"
    echo "  Admin UI: http://localhost:8082/admin"
    echo "  Prometheus: http://localhost:9090 (if enabled)"
    echo "  Grafana: http://localhost:3000 (if enabled)"
}

stop_services() {
    print_header "Stopping Services"

    cd "$PROJECT_ROOT"
    docker-compose down

    print_success "Services stopped"
}

run_tests() {
    print_header "Running Tests"

    # Test health endpoint
    print_info "Testing health endpoint..."
    if curl -sf http://localhost:8082/health > /dev/null 2>&1; then
        print_success "Health check passed"
    else
        print_error "Health check failed"
        return 1
    fi

    # Test chat completion
    print_info "Testing chat completion..."
    response=$(curl -s -X POST http://localhost:8082/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{
        "model": "anthropic/claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": "Say hello"}]
      }')

    if echo "$response" | grep -q "choices"; then
        print_success "Chat completion test passed"
        echo ""
        echo "Response:"
        echo "$response" | jq .
    else
        print_error "Chat completion test failed"
        echo "Response: $response"
        return 1
    fi
}

view_logs() {
    print_header "Server Logs"
    docker-compose logs -f fcc-server
}

show_help() {
    cat << EOF
${BLUE}free-claude-code Docker Deployment Script${NC}

Usage: ./scripts/docker-deploy.sh [COMMAND]

Commands:
  setup       Interactive setup wizard
  build       Build Docker image
  start       Start services with docker-compose
  stop        Stop services
  test        Run basic tests
  logs        View server logs
  help        Show this help message

Examples:
  # First-time setup
  ./scripts/docker-deploy.sh setup
  ./scripts/docker-deploy.sh build
  ./scripts/docker-deploy.sh start

  # Daily operations
  ./scripts/docker-deploy.sh logs
  ./scripts/docker-deploy.sh test
  ./scripts/docker-deploy.sh stop

Environment:
  .env.production     Configuration file (created during setup)
  Dockerfile          Docker image definition
  docker-compose.yml  Multi-container orchestration

Documentation:
  See DOCKER_DEPLOYMENT.md for complete documentation
EOF
}

# Main
main() {
    local command="${1:-help}"

    case "$command" in
        setup)
            check_dependencies
            setup_interactive
            ;;
        build)
            check_dependencies
            build_docker_image
            ;;
        start)
            check_dependencies
            start_services
            ;;
        stop)
            check_dependencies
            stop_services
            ;;
        test)
            check_dependencies
            run_tests
            ;;
        logs)
            check_dependencies
            view_logs
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
