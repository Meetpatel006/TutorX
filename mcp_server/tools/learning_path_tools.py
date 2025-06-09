"""
Learning path generation tools for TutorX.
"""
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
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
from resources.concept_graph import CONCEPT_GRAPH

# Import MCP
from mcp_server.mcp_instance import mcp
from mcp_server.model.gemini_flash import GeminiFlash

MODEL = GeminiFlash()

def get_prerequisites(concept_id: str, visited: Optional[set] = None) -> List[Dict[str, Any]]:
    """
    Get all prerequisites for a concept recursively.
    
    Args:
        concept_id: ID of the concept to get prerequisites for
        visited: Set of already visited concepts to avoid cycles
        
    Returns:
        List of prerequisite concepts in order
    """
    if visited is None:
        visited = set()
    
    if concept_id not in CONCEPT_GRAPH or concept_id in visited:
        return []
    
    visited.add(concept_id)
    prerequisites = []
    
    # Get direct prerequisites
    for prereq_id in CONCEPT_GRAPH[concept_id].get("prerequisites", []):
        if prereq_id in CONCEPT_GRAPH and prereq_id not in visited:
            prerequisites.extend(get_prerequisites(prereq_id, visited))
    
    # Add the current concept
    prerequisites.append(CONCEPT_GRAPH[concept_id])
    return prerequisites

def generate_learning_path(concept_ids: List[str], student_level: str = "beginner") -> Dict[str, Any]:
    """
    Generate a personalized learning path for a student.
    
    Args:
        concept_ids: List of concept IDs to include in the learning path
        student_level: Student's current level (beginner, intermediate, advanced)
        
    Returns:
        Dictionary containing the learning path
    """
    if not concept_ids:
        return {"error": "At least one concept ID is required"}
    
    # Get all prerequisites for each concept
    all_prerequisites = []
    visited = set()
    
    for concept_id in concept_ids:
        if concept_id in CONCEPT_GRAPH:
            prereqs = get_prerequisites(concept_id, visited)
            all_prerequisites.extend(prereqs)
    
    # Remove duplicates while preserving order
    unique_concepts = []
    seen = set()
    for concept in all_prerequisites:
        if concept["id"] not in seen:
            seen.add(concept["id"])
            unique_concepts.append(concept)
    
    # Add any target concepts not already in the path
    for concept_id in concept_ids:
        if concept_id in CONCEPT_GRAPH and concept_id not in seen:
            unique_concepts.append(CONCEPT_GRAPH[concept_id])
    
    # Estimate time required for each concept based on student level
    time_estimates = {
        "beginner": {"min": 30, "max": 60},    # 30-60 minutes per concept
        "intermediate": {"min": 20, "max": 45},  # 20-45 minutes per concept
        "advanced": {"min": 15, "max": 30}      # 15-30 minutes per concept
    }
    
    level = student_level.lower()
    if level not in time_estimates:
        level = "beginner"
    
    time_min = time_estimates[level]["min"]
    time_max = time_estimates[level]["max"]
    
    # Generate learning path with estimated times
    learning_path = []
    total_minutes = 0
    
    for i, concept in enumerate(unique_concepts, 1):
        # Random time estimate within range
        minutes = random.randint(time_min, time_max)
        total_minutes += minutes
        
        learning_path.append({
            "step": i,
            "concept_id": concept["id"],
            "concept_name": concept["name"],
            "description": concept.get("description", ""),
            "estimated_time_minutes": minutes,
            "resources": [
                f"Video tutorial on {concept['name']}",
                f"{concept['name']} documentation",
                f"Practice exercises for {concept['name']}"
            ]
        })
    
    # Calculate total time
    hours, minutes = divmod(total_minutes, 60)
    total_time = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    return {
        "learning_path": learning_path,
        "total_steps": len(learning_path),
        "total_time_minutes": total_minutes,
        "total_time_display": total_time,
        "student_level": student_level,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }

@mcp.tool()
async def get_learning_path(student_id: str, concept_ids: list, student_level: str = "beginner") -> dict:
    """
    Generate a personalized learning path for a student, fully LLM-driven.
    Use Gemini to generate a JSON object with a list of steps, each with concept name, description, estimated time, and recommended resources.
    """
    prompt = (
        f"A student (ID: {student_id}) with level '{student_level}' needs a learning path for these concepts: {concept_ids}. "
        f"Return a JSON object with a 'learning_path' field: a list of steps, each with concept_name, description, estimated_time_minutes, and resources (list)."
    )
    llm_response = await MODEL.generate_text(prompt)
    try:
        data = json.loads(llm_response)
    except Exception:
        data = {"llm_raw": llm_response, "error": "Failed to parse LLM output as JSON"}
    return data
