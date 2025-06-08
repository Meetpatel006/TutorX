"""
TutorX MCP Server - Main Entry Point

This is the main entry point for the TutorX MCP server.
It imports and runs the FastAPI application from the mcp_server package.
"""
import os
import uvicorn
from mcp_server import api_app, mcp

# Get server configuration from environment variables with defaults
SERVER_HOST = os.getenv("MCP_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("MCP_PORT", "8001"))
SERVER_TRANSPORT = os.getenv("MCP_TRANSPORT", "sse")

def run_server():
    """Run the MCP server with the configured settings."""
    print(f"Starting TutorX MCP server on {SERVER_HOST}:{SERVER_PORT}...")
    print(f"MCP transport: {SERVER_TRANSPORT}")
    print(f"API docs: http://{SERVER_HOST}:{SERVER_PORT}/docs")
    print(f"MCP endpoint: http://{SERVER_HOST}:{SERVER_PORT}/mcp")
    
    # Configure uvicorn to run the FastAPI app
    uvicorn.run(
        "server:api_app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    run_server()