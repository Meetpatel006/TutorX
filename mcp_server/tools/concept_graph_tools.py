"""
Concept graph tools for TutorX MCP.
"""
from typing import Dict, Any, Optional
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent
sys.path.insert(0, str(parent_dir))

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Import from local resources
from resources import concept_graph

# Import MCP
from mcp_server.mcp_instance import mcp

@mcp.tool()
async def get_concept_graph_tool(concept_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the complete concept graph or a specific concept.
    
    Args:
        concept_id: Optional concept ID to get a specific concept
        
    Returns:
        Dictionary containing the concept graph or a specific concept
    """
    if concept_id:
        concept = concept_graph.get_concept(concept_id)
        if not concept:
            return {"error": f"Concept {concept_id} not found"}
        return {"concept": concept}
    
    return {"concepts": list(concept_graph.get_concept_graph().values())}
