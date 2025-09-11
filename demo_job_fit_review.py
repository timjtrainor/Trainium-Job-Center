#!/usr/bin/env python3
"""
End-to-end demonstration of Job Fit Review multi-model agents and MCP gateway.

This script demonstrates:
1. Different AI models configured for different agents
2. MCP gateway tool integration
3. Extensible architecture for adding new MCP servers

Run this after starting services with: docker-compose up --build
"""

import asyncio
import json
import sys
from pathlib import Path
import yaml

def show_agent_model_configurations():
    """Display the different model configurations for each agent"""
    print("🤖 AGENT MODEL CONFIGURATIONS")
    print("="*50)
    
    base_dir = Path("python-service/app/services/crewai")
    agents = ["researcher", "negotiator", "skeptic"]
    
    for agent in agents:
        agent_file = base_dir / "agents" / f"{agent}.yaml"
        with open(agent_file, 'r') as f:
            config = yaml.safe_load(f)
        
        provider = config["models"][0]["provider"]
        model = config["models"][0]["model"]
        tools = config.get("tools", [])
        role = config.get("role", "N/A")
        
        print(f"\n🔸 {agent.upper()} Agent")
        print(f"   Role: {role}")
        print(f"   Model: {provider}:{model}")
        print(f"   Tools: {', '.join(tools)}")

def show_mcp_architecture():
    """Display the MCP gateway architecture"""
    print("\n\n🌐 MCP GATEWAY ARCHITECTURE")
    print("="*50)
    
    print("""
    CrewAI Agents → MCP Gateway Tool → MCP Gateway Service → MCP Servers
                                                            ├── DuckDuckGo ✅
                                                            ├── [Future Server]
                                                            └── [Future Server]
    
    🔧 Current Implementation:
    • MCP Gateway Service: docker/mcp-gateway/
    • CrewAI Tool: python-service/app/services/crewai/tools/mcp_gateway.py
    • Docker Service: mcp-gateway (port 8811)
    • Default MCP Server: DuckDuckGo search
    """)

def show_extensibility_guide():
    """Show how to add new MCP servers"""
    print("\n\n📚 ADDING NEW MCP SERVERS")
    print("="*50)
    
    print("""
    Step 1: Update server configuration
    File: docker/mcp-gateway/config/servers.yaml
    
    servers:
      filesystem:
        description: "Filesystem operations MCP server"
        command: "npx"
        args: ["-y", "@modelcontextprotocol/server-filesystem@latest"]
        env:
          ALLOWED_DIRECTORIES: "/tmp,/app/data"
        auto_start: false
    
    Step 2: Update gateway code
    File: docker/mcp-gateway/main.py
    
    Add to MCP_SERVERS_CONFIG dictionary.
    
    Step 3: Use in agents
    File: agents/[agent_name].yaml
    
    tools:
      - web_search     # DuckDuckGo via MCP
      - filesystem     # New MCP server
    
    🔗 See MCP_INTEGRATION_GUIDE.md for complete instructions.
    """)

def show_validation_results():
    """Show validation results"""
    print("\n\n✅ VALIDATION RESULTS")
    print("="*50)
    
    # Run our validation script
    import subprocess
    
    try:
        result = subprocess.run([
            "python", "python-service/validate_implementation.py"
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("🎉 All validations passed!")
            # Extract the summary section
            lines = result.stdout.split('\n')
            summary_started = False
            for line in lines:
                if "VALIDATION SUMMARY" in line:
                    summary_started = True
                if summary_started:
                    print(line)
        else:
            print("⚠️ Some validations failed:")
            print(result.stdout)
            
    except Exception as e:
        print(f"❌ Could not run validation: {e}")

def show_usage_examples():
    """Show usage examples"""
    print("\n\n💡 USAGE EXAMPLES")
    print("="*50)
    
    print("""
    1. Start the services:
       docker-compose up --build
    
    2. Test MCP gateway health:
       curl http://localhost:8811/health
    
    3. Test web search via MCP:
       curl -X POST http://localhost:8811/call \\
         -H "Content-Type: application/json" \\
         -d '{
           "server": "duckduckgo",
           "method": "search",
           "params": {"query": "Python programming", "max_results": 3}
         }'
    
    4. Use in CrewAI agent:
       from app.services.crewai.tools.mcp_gateway import create_mcp_gateway_tool
       
       tool = create_mcp_gateway_tool()
       result = tool._execute("AI trends 2024", server="duckduckgo")
       print(result)
    
    5. Run job review with different models:
       from app.services.crewai.job_review.crew import get_job_review_crew
       
       crew = get_job_review_crew()
       result = crew.job_review().kickoff({
           "job": {
               "title": "Senior Python Developer",
               "company": "Tech Corp",
               "description": "Build AI applications..."
           }
       })
    """)

def show_model_routing_demo():
    """Demonstrate model routing"""
    print("\n\n🎯 MODEL ROUTING DEMONSTRATION")
    print("="*50)
    
    print("""
    When a CrewAI job review runs:
    
    1. 🔍 RESEARCHER Agent (OpenAI GPT-4o-mini)
       ├── Uses web_search tool → MCP Gateway → DuckDuckGo
       ├── Analyzes job requirements and skills
       └── Provides research-based insights
    
    2. 💰 NEGOTIATOR Agent (Google Gemini-1.5-flash)  
       ├── Uses chroma_search for compensation data
       ├── Evaluates salary and benefits
       └── Provides negotiation strategy
    
    3. 🤔 SKEPTIC Agent (Ollama Gemma3:1b)
       ├── Uses chroma_search for risk assessment
       ├── Identifies potential red flags
       └── Provides critical evaluation
    
    Each agent automatically uses its configured model without code changes!
    """)

def main():
    """Run the complete demonstration"""
    print("🚀 JOB FIT REVIEW: MULTI-MODEL AGENTS & MCP GATEWAY")
    print("="*70)
    
    try:
        show_agent_model_configurations()
        show_mcp_architecture()
        show_model_routing_demo()
        show_validation_results()
        show_extensibility_guide()
        show_usage_examples()
        
        print("\n\n🎯 SUMMARY")
        print("="*50)
        print("""
        ✅ Multi-model agent configuration implemented
        ✅ MCP gateway service created with DuckDuckGo integration
        ✅ CrewAI tool for MCP gateway connectivity
        ✅ Extensible architecture for adding new MCP servers
        ✅ Comprehensive documentation and validation
        
        🚀 Ready to use! Start with: docker-compose up --build
        """)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())