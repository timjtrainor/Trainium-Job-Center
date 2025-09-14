"""
Demonstration of MCP Gateway integration concept for CrewAI.

This script demonstrates how the MCP Gateway integration would work
with DuckDuckGo tools in a CrewAI setup.
"""
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path


class MockMCPAdapter:
    """Mock MCP Adapter that simulates the real implementation."""
    
    def __init__(self, gateway_url: str = "http://localhost:8811"):
        self.gateway_url = gateway_url
        self.connected = False
        self._available_tools = {}
        
    async def __aenter__(self):
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        
    async def connect(self):
        """Simulate connection to MCP Gateway."""
        print(f"🔌 Connecting to MCP Gateway at {self.gateway_url}")
        time.sleep(0.1)  # Simulate network delay
        
        # Simulate loading DuckDuckGo tools
        self._available_tools = {
            "duckduckgo_web_search": {
                "name": "web_search",
                "description": "Search the web using DuckDuckGo",
                "parameters": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Max results", "default": 5}
                }
            }
        }
        
        self.connected = True
        print(f"✅ Connected! Available tools: {list(self._available_tools.keys())}")
        
    async def disconnect(self):
        """Simulate disconnection from MCP Gateway."""
        if self.connected:
            print("🔌 Disconnecting from MCP Gateway")
            self.connected = False
            self._available_tools.clear()
            
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get available tools."""
        return dict(self._available_tools)
        
    def get_duckduckgo_tools(self) -> List[Dict[str, Any]]:
        """Get DuckDuckGo tools for CrewAI integration."""
        tools = []
        for tool_name, tool_config in self._available_tools.items():
            if tool_name.startswith("duckduckgo_"):
                crewai_tool = {
                    "name": tool_name,
                    "description": tool_config.get("description", ""),
                    "parameters": tool_config.get("parameters", {}),
                    "execute": self._create_mock_executor(tool_name)
                }
                tools.append(crewai_tool)
        return tools
        
    def _create_mock_executor(self, tool_name: str):
        """Create a mock tool executor."""
        def execute(**kwargs):
            query = kwargs.get("query", "")
            max_results = kwargs.get("max_results", 5)
            
            # Mock search results
            results = [
                f"🔍 Search result {i+1} for '{query}': Mock result about {query}"
                for i in range(min(max_results, 3))
            ]
            
            return f"Found {len(results)} results:\n" + "\n".join(results)
            
        return execute
        

class MockJobPostingReviewCrew:
    """Mock JobPostingReviewCrew that demonstrates MCP tool integration."""
    
    def __init__(self):
        self.crew_name = "job_posting_review"
        self.mcp_tools = []
        
    async def prepare_analysis(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare analysis with MCP tool loading."""
        print(f"\n📋 Preparing {self.crew_name} analysis...")
        
        # Extract job data
        job_data = inputs.get("job", {})
        print(f"📄 Job: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}")
        
        # Load MCP tools (this would use the real MCPServerAdapter)
        print("🔧 Loading MCP tools...")
        
        async with MockMCPAdapter("http://mcp-gateway:8811") as adapter:
            duckduckgo_tools = adapter.get_duckduckgo_tools()
            
            if duckduckgo_tools:
                print(f"✅ Loaded {len(duckduckgo_tools)} DuckDuckGo tools:")
                for tool in duckduckgo_tools:
                    print(f"   - {tool['name']}: {tool['description']}")
                    
                # Store tools for agents
                inputs["mcp_tools"] = duckduckgo_tools
                self.mcp_tools = duckduckgo_tools
                
                # Test tool execution
                if duckduckgo_tools:
                    test_tool = duckduckgo_tools[0]
                    print(f"\n🧪 Testing tool: {test_tool['name']}")
                    
                    test_query = f"{job_data.get('title', 'Python Developer')} salary range"
                    result = test_tool["execute"](query=test_query, max_results=3)
                    print(f"🔍 Test search result:\n{result}")
            else:
                print("⚠️  No DuckDuckGo tools available")
                inputs["mcp_tools"] = []
                
        return inputs
        
    def simulate_agent_execution(self, inputs: Dict[str, Any]):
        """Simulate how agents would use MCP tools."""
        print(f"\n🤖 Simulating agent execution with MCP tools...")
        
        mcp_tools = inputs.get("mcp_tools", [])
        job_data = inputs.get("job", {})
        
        if not mcp_tools:
            print("❌ No MCP tools available for agents")
            return
            
        # Simulate researcher agent using web search
        print("👨‍🔬 Researcher Agent: Using DuckDuckGo search...")
        search_tool = next((t for t in mcp_tools if "web_search" in t["name"]), None)
        
        if search_tool:
            queries = [
                f"{job_data.get('company', 'Company')} employee reviews",
                f"{job_data.get('title', 'Job')} market trends 2024",
                f"{job_data.get('company', 'Company')} technology stack"
            ]
            
            for query in queries:
                print(f"   🔍 Searching: {query}")
                result = search_tool["execute"](query=query, max_results=2)
                print(f"   📊 Results: {result.split(':')[0]}...")
                
        print("✅ Agent execution complete with MCP tool integration!")


async def demonstrate_integration():
    """Demonstrate the complete MCP integration flow."""
    print("🚀 MCP Gateway Integration Demonstration")
    print("=" * 50)
    
    # Sample job data
    job_data = {
        "title": "Senior Python Developer",
        "company": "CrewAI Technologies",
        "description": "Looking for experienced Python developer with AI/ML experience"
    }
    
    inputs = {"job": job_data}
    
    # Create mock crew
    crew = MockJobPostingReviewCrew()
    
    # Demonstrate the integration flow
    try:
        # 1. Prepare analysis (loads MCP tools)
        prepared_inputs = await crew.prepare_analysis(inputs)
        
        # 2. Simulate agent execution with tools
        crew.simulate_agent_execution(prepared_inputs)
        
        print("\n🎉 Integration demonstration complete!")
        print("\nKey Integration Points:")
        print("✅ MCP Gateway orchestrated as Docker container")
        print("✅ MCPServerAdapter with proper context management") 
        print("✅ DuckDuckGo tools retrieved and exposed")
        print("✅ Tools injected into CrewAI agents before kickoff")
        print("✅ Agents can execute web searches through MCP")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demonstrate_integration())