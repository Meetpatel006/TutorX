"""
Concept-related MCP tools for TutorX.
"""
import random
from typing import Dict, Any, Optional
from datetime import datetime, timezone
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
from resources.concept_graph import get_concept, get_all_concepts

# Import MCP
from mcp_server.mcp_instance import mcp

@mcp.tool()
async def get_concept_tool(concept_id: str = None) -> Dict[str, Any]:
    """
    Get a specific concept or all concepts from the knowledge graph.
    
    Args:
        concept_id: Optional concept ID to retrieve a specific concept
        
    Returns:
        Dictionary containing the requested concept(s)
    """
    if concept_id:
        concept = get_concept(concept_id)
        if not concept:
            return {"error": f"Concept {concept_id} not found"}
        return {"concept": concept}
    return get_all_concepts()

@mcp.tool()
async def assess_skill_tool(student_id: str, concept_id: str) -> Dict[str, Any]:
    """
    Assess a student's understanding of a specific concept.
    
    Args:
        student_id: Unique identifier for the student
        concept_id: ID of the concept to assess
        
    Returns:
        Dictionary containing assessment results
    """
    # Get concept data
    concept_data = get_concept(concept_id)
    if not concept_data:
        return {"error": f"Cannot assess skill: Concept {concept_id} not found"}
    
    concept_name = concept_data.get("name", concept_id)
    
    # Generate a score based on concept difficulty or random
    score = random.uniform(0.2, 1.0)  # Random score between 0.2 and 1.0
    
    # Set timestamp with timezone
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Generate feedback based on score
    feedback = {
        "strengths": [f"Good understanding of {concept_name} fundamentals"],
        "areas_for_improvement": [f"Could work on advanced applications of {concept_name}"],
        "recommendations": [
            f"Review {concept_name} practice problems",
            f"Watch tutorial videos on {concept_name}"
        ]
    }
    
    # Adjust feedback based on score
    if score < 0.5:
        feedback["strengths"] = [f"Basic understanding of {concept_name}"]
        feedback["areas_for_improvement"] = [
            f"Needs to strengthen fundamental knowledge of {concept_name}",
            f"Practice more exercises on {concept_name}"
        ]
    
    # Return assessment results
    return {
        "student_id": student_id,
        "concept_id": concept_id,
        "concept_name": concept_name,
        "score": round(score, 2),  # Round to 2 decimal places
        "timestamp": timestamp,
        "feedback": feedback
    }
