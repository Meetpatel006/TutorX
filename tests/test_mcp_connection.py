"""
Test MCP connection and tool availability.
"""
import asyncio
import json
from mcp import ClientSession
from mcp.client.sse import sse_client

SERVER_URL = "http://localhost:8000/sse"

async def test_mcp_connection():
    """Test MCP connection and list available tools."""
    print("🔗 Testing MCP Connection")
    print("=" * 40)
    
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                
                # List available tools
                print("📋 Available Tools:")
                tools = session.list_tools()
                if hasattr(tools, 'tools'):
                    for tool in tools.tools:
                        print(f"  ✅ {tool.name}")
                else:
                    print(f"  Tools response: {tools}")
                
                # Test calling start_adaptive_session
                print("\n🧪 Testing start_adaptive_session tool...")
                try:
                    response = await session.call_tool("start_adaptive_session", {
                        "student_id": "test_student",
                        "concept_id": "test_concept",
                        "initial_difficulty": 0.5
                    })
                    print(f"  ✅ Tool call successful: {response}")
                except Exception as e:
                    print(f"  ❌ Tool call failed: {e}")
                
                # Test calling get_learning_path (existing tool)
                print("\n🧪 Testing get_learning_path tool...")
                try:
                    response = await session.call_tool("get_learning_path", {
                        "student_id": "test_student",
                        "concept_ids": ["test_concept"],
                        "student_level": "beginner"
                    })
                    print(f"  ✅ Tool call successful: {type(response)}")
                except Exception as e:
                    print(f"  ❌ Tool call failed: {e}")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())
