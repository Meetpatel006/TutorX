from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "TutorX",
    dependencies=["mcp[cli]>=1.9.3"],
    cors_origins=["*"]
) 