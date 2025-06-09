"""
Concept graph tools for TutorX MCP.
"""
from typing import Dict, Any, Optional
import sys
import os
from pathlib import Path
import json

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
from mcp_server.model.gemini_flash import GeminiFlash

MODEL = GeminiFlash()

@mcp.tool()
async def get_concept_graph_tool(concept_id: Optional[str] = None) -> dict:
    """
    Get the complete concept graph or a specific concept, fully LLM-driven.
    For a specific concept, use Gemini to generate a JSON object with explanation, related concepts, prerequisites, and summary.
    For the full graph, use Gemini to generate a JSON object with a list of all concepts and their relationships.
    """
    if concept_id:
        prompt = (
            f"Provide a JSON object for the concept '{concept_id}' with fields: explanation (string), related_concepts (list of strings), prerequisites (list of strings), and summary (string)."
        )
    else:
        prompt = (
            "Provide a JSON object with a list of all concepts in a knowledge graph. "
            "Each concept should have fields: id, name, description, related_concepts (list), prerequisites (list)."
        )
    llm_response = await MODEL.generate_text(prompt)
    try:
        data = json.loads(llm_response)
    except Exception:
        data = {"llm_raw": llm_response, "error": "Failed to parse LLM output as JSON"}
    return data
