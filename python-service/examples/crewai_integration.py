#!/usr/bin/env python3
"""CrewAI Integration Example.

This example demonstrates how to integrate MCP Gateway tools with CrewAI
agents and crews, showing both sync and async patterns.
"""

import asyncio
import sys
import os
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crewai import Agent, Task, Crew, Process

from app.services.mcp import (
    MCPGatewayAdapter,
    MCPConfig,
    StreamingTransport,
    AsyncMCPToolWrapper,
    MCPToolWrapper,
    MCPToolFactory,
    ConnectionError
)


async def crewai_integration_example():
    """Main CrewAI integration example."""
    print("🤖 CrewAI MCP Integration Example")
    print("=" * 50)
    
    # Initialize MCP adapter
    print("\n🔧 Initializing MCP Gateway connection...")
    transport = StreamingTransport("http://localhost:8811")
    adapter = MCPGatewayAdapter(transport=transport, timeout=30)
    
    try:
        async with adapter:
            print("✓ Connected to MCP Gateway")
            
            # Create CrewAI-compatible tools
            print("\n🛠️  Creating CrewAI tools...")
            factory = MCPToolFactory(adapter)
            mcp_tools = await factory.create_crewai_tools()
            
            print(f"✓ Created {len(mcp_tools)} CrewAI tools:")
            for tool_name, tool in mcp_tools.items():
                print(f"  - {tool_name}: {tool.description}")
            
            if not mcp_tools:
                print("⚠️  No tools available - running with basic agents")
                tools_list = []
            else:
                tools_list = list(mcp_tools.values())
            
            # Create specialized agents
            researcher = Agent(
                role='Research Specialist',
                goal='Conduct thorough research using available MCP tools',
                backstory="""You are an expert researcher with access to various 
                research tools through the MCP Gateway. You excel at finding, 
                analyzing, and synthesizing information from multiple sources.""",
                tools=tools_list,
                verbose=True
            )
            
            analyst = Agent(
                role='Data Analyst',
                goal='Analyze and interpret research findings',
                backstory="""You are a skilled data analyst who specializes in 
                interpreting research results and providing actionable insights. 
                You work closely with researchers to understand their findings.""",
                tools=tools_list[:2] if len(tools_list) > 2 else tools_list,  # Subset of tools
                verbose=True
            )
            
            writer = Agent(
                role='Technical Writer',
                goal='Create comprehensive reports from research and analysis',
                backstory="""You are a technical writer who excels at creating 
                clear, comprehensive reports that synthesize complex research 
                and analysis into actionable recommendations.""",
                verbose=True
            )
            
            # Create tasks
            research_task = Task(
                description="""Research the capabilities and features of MCP 
                (Model Context Protocol) gateways. Focus on:
                1. Core functionality and architecture
                2. Integration patterns with AI frameworks
                3. Available tools and their purposes
                4. Best practices for implementation
                
                Use available MCP tools if possible to gather information.""",
                agent=researcher,
                expected_output="""A detailed research summary covering MCP gateway 
                capabilities, architecture, integration patterns, and available tools."""
            )
            
            analysis_task = Task(
                description="""Analyze the research findings about MCP gateways 
                and identify:
                1. Key strengths and advantages
                2. Potential limitations or challenges
                3. Use cases and applications
                4. Integration recommendations
                
                Provide specific insights about how MCP gateways can enhance 
                AI agent workflows.""",
                agent=analyst,
                expected_output="""An analytical report with insights about MCP 
                gateway strengths, limitations, use cases, and integration recommendations."""
            )
            
            writing_task = Task(
                description="""Create a comprehensive technical report that combines 
                the research findings and analysis into a cohesive document. Include:
                1. Executive summary
                2. Technical overview of MCP gateways
                3. Key findings and insights
                4. Practical recommendations
                5. Conclusion
                
                The report should be suitable for technical stakeholders.""",
                agent=writer,
                expected_output="""A well-structured technical report about MCP 
                gateways with executive summary, technical details, and recommendations."""
            )
            
            # Create and execute crew
            print("\n🚀 Executing CrewAI crew with MCP tools...")
            crew = Crew(
                agents=[researcher, analyst, writer],
                tasks=[research_task, analysis_task, writing_task],
                process=Process.sequential,
                verbose=True
            )
            
            # Execute the crew
            try:
                result = crew.kickoff()
                print("\n✅ CrewAI execution completed!")
                print("=" * 50)
                print("📄 Final Report:")
                print("=" * 50)
                print(result)
                
            except Exception as e:
                print(f"❌ CrewAI execution failed: {e}")
                print("💡 This might be due to tool execution issues or agent configuration")
                
    except ConnectionError as e:
        print(f"❌ MCP Gateway connection failed: {e}")
        print("💡 Make sure the MCP Gateway is running on http://localhost:8811")
        print("   You can start it with: python mcp_gateway.py")
        
        # Show example of offline crew without MCP tools
        await offline_crew_example()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def async_tool_example():
    """Demonstrate async MCP tool usage (for async-native frameworks)."""
    print("\n🔄 Async MCP Tool Example")
    print("=" * 35)
    
    transport = StreamingTransport("http://localhost:8811")
    adapter = MCPGatewayAdapter(transport=transport)
    
    try:
        async with adapter:
            print("✓ Connected for async tool demonstration")
            
            # Create async tools
            factory = MCPToolFactory(adapter)
            async_tools = await factory.create_async_tools()
            
            if async_tools:
                tool_name = list(async_tools.keys())[0]
                tool = async_tools[tool_name]
                
                print(f"\n🔍 Testing async tool: {tool_name}")
                print(f"   Description: {tool.get_description()}")
                
                # Get tool schema
                schema = tool.get_schema()
                print(f"   Schema: {schema}")
                
                # Create example arguments
                example_args = {}
                properties = schema.get("properties", {})
                for prop_name, prop_info in properties.items():
                    if prop_info.get("type") == "string":
                        example_args[prop_name] = "example search query"
                        break
                
                # Execute async tool
                if example_args:
                    try:
                        result = await tool.execute(**example_args)
                        print(f"✓ Async execution successful!")
                        print(f"   Result: {result[:200]}{'...' if len(result) > 200 else ''}")
                    except Exception as e:
                        print(f"⚠️  Async execution failed: {e}")
                else:
                    print("ℹ️  No suitable arguments for tool execution")
            else:
                print("ℹ️  No async tools available")
                
    except ConnectionError:
        print("ℹ️  Gateway not available for async tool example")


async def offline_crew_example():
    """Example crew that works without MCP tools (fallback)."""
    print("\n🔄 Offline CrewAI Example (No MCP Tools)")
    print("=" * 45)
    
    # Create agents without MCP tools
    knowledge_agent = Agent(
        role='Knowledge Expert',
        goal='Provide information about MCP and AI integration patterns',
        backstory="""You are a knowledgeable expert in AI systems and integration 
        patterns. You have extensive knowledge about protocols like MCP and how 
        they enable tool integration in AI workflows.""",
        verbose=True
    )
    
    # Simple task without external tools
    knowledge_task = Task(
        description="""Based on your knowledge, explain what MCP (Model Context Protocol) 
        is and how it benefits AI agent workflows. Include:
        1. What MCP is and its purpose
        2. Key benefits for AI agents
        3. Common integration patterns
        4. Why it's useful for tool access""",
        agent=knowledge_agent,
        expected_output="""A clear explanation of MCP and its benefits for AI workflows."""
    )
    
    # Execute simple crew
    simple_crew = Crew(
        agents=[knowledge_agent],
        tasks=[knowledge_task],
        verbose=True
    )
    
    try:
        result = simple_crew.kickoff()
        print("\n✅ Offline crew completed!")
        print("=" * 30)
        print(result)
    except Exception as e:
        print(f"❌ Offline crew failed: {e}")


async def tool_factory_demo():
    """Demonstrate tool factory capabilities."""
    print("\n🏭 Tool Factory Demonstration")
    print("=" * 35)
    
    transport = StreamingTransport("http://localhost:8811")
    adapter = MCPGatewayAdapter(transport=transport)
    
    try:
        async with adapter:
            factory = MCPToolFactory(adapter)
            
            # Demonstrate bulk tool creation
            print("🔨 Creating all available tools...")
            async_tools = await factory.create_async_tools()
            crewai_tools = await factory.create_crewai_tools()
            
            print(f"✓ Created {len(async_tools)} async wrappers")
            print(f"✓ Created {len(crewai_tools)} CrewAI wrappers")
            
            # Demonstrate single tool creation
            if async_tools:
                tool_name = list(async_tools.keys())[0]
                print(f"\n🎯 Creating single tool: {tool_name}")
                
                single_async = await factory.create_single_async_tool(tool_name)
                single_crewai = factory.create_single_crewai_tool(tool_name)
                
                print(f"✓ Single async tool: {single_async.get_description()}")
                print(f"✓ Single CrewAI tool: {single_crewai.description}")
                
    except ConnectionError:
        print("ℹ️  Gateway not available for tool factory demo")


async def main():
    """Run all CrewAI integration examples."""
    print("🚀 CrewAI MCP Integration Examples")
    print("=" * 50)
    
    # Main integration example
    await crewai_integration_example()
    
    # Async tool demonstration
    await async_tool_example()
    
    # Tool factory demonstration
    await tool_factory_demo()
    
    print("\n✨ CrewAI integration examples completed!")
    print("\nKey takeaways:")
    print("1. MCP tools can be seamlessly integrated with CrewAI agents")
    print("2. Both sync and async patterns are supported")
    print("3. Tool factory provides convenient bulk operations")
    print("4. Graceful fallback when MCP Gateway is unavailable")


if __name__ == "__main__":
    asyncio.run(main())