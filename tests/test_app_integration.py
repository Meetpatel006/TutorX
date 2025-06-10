"""
Test the app integration with the new adaptive learning tools.
"""
import asyncio
import json
from mcp import ClientSession
from mcp.client.sse import sse_client

SERVER_URL = "http://localhost:8000/sse"

async def extract_response_content(response):
    """Helper function to extract content from MCP response (same as app.py)"""
    # Handle direct dictionary responses (new format)
    if isinstance(response, dict):
        return response
    
    # Handle MCP response with content structure (CallToolResult format)
    if hasattr(response, 'content') and isinstance(response.content, list):
        for item in response.content:
            # Handle TextContent objects
            if hasattr(item, 'text') and item.text:
                try:
                    return json.loads(item.text)
                except Exception as e:
                    return {"raw_pretty": item.text, "parse_error": str(e)}
            # Handle other content types
            elif hasattr(item, 'type') and item.type == 'text':
                try:
                    return json.loads(str(item))
                except Exception:
                    return {"raw_pretty": str(item)}
    
    # Handle string responses
    if isinstance(response, str):
        try:
            return json.loads(response)
        except Exception:
            return {"raw_pretty": response}
    
    # Handle any other response type - try to extract useful information
    if hasattr(response, '__dict__'):
        return {"raw_pretty": json.dumps(str(response), indent=2), "type": type(response).__name__}
    
    return {"raw_pretty": str(response), "type": type(response).__name__}

async def start_adaptive_session_async(student_id, concept_id, difficulty):
    try:
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                result = await session.call_tool("start_adaptive_session", {
                    "student_id": student_id,
                    "concept_id": concept_id,
                    "initial_difficulty": float(difficulty)
                })
                return await extract_response_content(result)
    except Exception as e:
        return {"error": str(e)}

async def get_adaptive_learning_path_async(student_id, concept_ids, strategy, max_concepts):
    try:
        # Parse concept_ids if it's a string
        if isinstance(concept_ids, str):
            concept_ids = [c.strip() for c in concept_ids.split(',') if c.strip()]
        
        async with sse_client(SERVER_URL) as (sse, write):
            async with ClientSession(sse, write) as session:
                await session.initialize()
                result = await session.call_tool("get_adaptive_learning_path", {
                    "student_id": student_id,
                    "target_concepts": concept_ids,
                    "strategy": strategy,
                    "max_concepts": int(max_concepts)
                })
                return await extract_response_content(result)
    except Exception as e:
        return {"error": str(e)}

async def test_app_integration():
    """Test the app integration with adaptive learning tools."""
    print("🧪 Testing App Integration with Adaptive Learning")
    print("=" * 50)
    
    # Test 1: Start adaptive session (like the app would)
    print("\n1. Testing start_adaptive_session_async...")
    session_result = await start_adaptive_session_async(
        student_id="app_test_student",
        concept_id="algebra_basics",
        difficulty=0.6
    )
    print(f"Result: {json.dumps(session_result, indent=2)}")
    
    # Test 2: Get adaptive learning path (like the app would)
    print("\n2. Testing get_adaptive_learning_path_async...")
    path_result = await get_adaptive_learning_path_async(
        student_id="app_test_student",
        concept_ids="algebra_basics,linear_equations,quadratic_equations",
        strategy="adaptive",
        max_concepts=5
    )
    print(f"Result: {json.dumps(path_result, indent=2)}")
    
    print("\n✅ App integration tests completed!")

if __name__ == "__main__":
    asyncio.run(test_app_integration())
