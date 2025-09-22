#!/bin/bash
# Setup script for MCP Gateway and required MCP server images

echo "🚀 Setting up MCP Gateway and Server Images"
echo "============================================"

# Function to check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "❌ Docker daemon is not running or not accessible"
        exit 1
    fi
    
    echo "✅ Docker is available"
}

# Function to pull MCP images
pull_mcp_images() {
    echo ""
    echo "📦 Pulling required MCP server images..."
    
    images=(
        "docker/mcp-gateway"
        "mcp/duckduckgo"
        "stickerdaniel/linkedin-mcp-server"
    )
    
    for image in "${images[@]}"; do
        echo "   Pulling $image..."
        if docker pull "$image"; then
            echo "   ✅ Successfully pulled $image"
        else
            echo "   ⚠️  Failed to pull $image (will be pulled on first use)"
        fi
    done
}

# Function to validate configuration
validate_config() {
    echo ""
    echo "🔍 Validating MCP configuration..."
    
    config_file="python-service/mcp-config/servers.json"
    if [ -f "$config_file" ]; then
        echo "   ✅ Found MCP server configuration: $config_file"
        
        # Check if it's valid JSON
        if python3 -m json.tool "$config_file" > /dev/null 2>&1; then
            echo "   ✅ Configuration file is valid JSON"
        else
            echo "   ❌ Configuration file has invalid JSON syntax"
            return 1
        fi
    else
        echo "   ❌ MCP server configuration not found: $config_file"
        return 1
    fi
    
    # Check docker-compose file
    if [ -f "docker-compose.yml" ]; then
        echo "   ✅ Found docker-compose.yml"
        
        # Check if mcp-gateway service is defined
        if grep -q "mcp-gateway:" docker-compose.yml; then
            echo "   ✅ MCP Gateway service is configured"
        else
            echo "   ❌ MCP Gateway service not found in docker-compose.yml"
            return 1
        fi
    else
        echo "   ❌ docker-compose.yml not found"
        return 1
    fi
}

# Function to test MCP server images
test_mcp_servers() {
    echo ""
    echo "🧪 Testing MCP server images..."
    
    # Test DuckDuckGo server
    echo "   Testing mcp/duckduckgo..."
    if timeout 10 docker run --rm mcp/duckduckgo --help > /dev/null 2>&1; then
        echo "   ✅ DuckDuckGo MCP server is working"
    else
        echo "   ⚠️  DuckDuckGo MCP server test failed or timed out"
    fi
    
    # Test LinkedIn server (just check if it starts)
    echo "   Testing stickerdaniel/linkedin-mcp-server..."
    if docker inspect stickerdaniel/linkedin-mcp-server > /dev/null 2>&1; then
        echo "   ✅ LinkedIn MCP server image is available"
    else
        echo "   ⚠️  LinkedIn MCP server image not available"
    fi
}

# Function to show startup instructions
show_instructions() {
    echo ""
    echo "🎉 Setup completed!"
    echo "=================="
    echo ""
    echo "To start the MCP Gateway and services:"
    echo "   docker-compose up -d"
    echo ""
    echo "To view MCP Gateway logs:"
    echo "   docker logs -f trainium_mcp_gateway"
    echo ""
    echo "To test the gateway health:"
    echo "   curl http://localhost:8811/health"
    echo ""
    echo "To stop the services:"
    echo "   docker-compose down"
    echo ""
    echo "📋 Configuration details:"
    echo "   - Gateway URL: http://localhost:8811"
    echo "   - Transport: stdio (internal) + HTTP REST API (external)"
    echo "   - Configured servers: duckduckgo, linkedin-mcp-server"
    echo "   - Verbose logging enabled for debugging"
}

# Main execution
main() {
    check_docker
    pull_mcp_images
    validate_config
    test_mcp_servers
    show_instructions
    
    echo ""
    echo "✅ MCP Gateway setup completed successfully!"
}

# Run main function
main