"""
TutorX MCP Server
"""
from mcp.server.fastmcp import FastMCP
import json
import os
import warnings
import uvicorn
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Filter out the tool registration warning
warnings.filterwarnings("ignore", message="Tool already exists")

# Import utility functions
from utils.multimodal import (
    process_text_query,
    process_voice_input,
    process_handwriting,
    generate_speech_response
)
from utils.assessment import (
    generate_question,
    evaluate_student_answer,
    generate_performance_analytics,
    detect_plagiarism
)
from typing import List, Dict, Any, Optional, Union
import random
from datetime import datetime, timedelta, timezone

# Get server configuration from environment variables with defaults
SERVER_HOST = os.getenv("MCP_HOST", "0.0.0.0")  # Allow connections from any IP
SERVER_PORT = int(os.getenv("MCP_PORT", "8001"))  # Changed default port to 8001
SERVER_TRANSPORT = os.getenv("MCP_TRANSPORT", "http")

# Create FastAPI app
api_app = FastAPI(title="TutorX MCP Server", version="1.0.0")

# Add CORS middleware
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the TutorX MCP server with explicit configuration
mcp = FastMCP(
    "TutorX",
    dependencies=["mcp[cli]>=1.9.3", "gradio>=4.19.0", "numpy>=1.24.0", "pillow>=10.0.0"],
    host=SERVER_HOST,
    port=SERVER_PORT,
    transport=SERVER_TRANSPORT,
    cors_origins=["*"]  # Allow CORS from any origin
)

# For FastMCP, we'll use it directly without mounting
# as it already creates its own FastAPI app internally

# ------------------ Core Features ------------------

# Store the concept graph data in memory
CONCEPT_GRAPH = {
    "python": {
        "id": "python",
        "name": "Python Programming",
        "description": "Fundamentals of Python programming language",
        "prerequisites": [],
        "related": ["functions", "oop", "data_structures"]
    },
    "functions": {
        "id": "functions",
        "name": "Python Functions",
        "description": "Creating and using functions in Python",
        "prerequisites": ["python"],
        "related": ["decorators", "lambdas"]
    },
    "oop": {
        "id": "oop",
        "name": "Object-Oriented Programming",
        "description": "Classes and objects in Python",
        "prerequisites": ["python"],
        "related": ["inheritance", "polymorphism"]
    },
    "data_structures": {
        "id": "data_structures",
        "name": "Data Structures",
        "description": "Built-in data structures in Python",
        "prerequisites": ["python"],
        "related": ["algorithms"]
    },
    "decorators": {
        "id": "decorators",
        "name": "Python Decorators",
        "description": "Function decorators in Python",
        "prerequisites": ["functions"],
        "related": ["python", "functions"]
    },
    "lambdas": {
        "id": "lambdas",
        "name": "Lambda Functions",
        "description": "Anonymous functions in Python",
        "prerequisites": ["functions"],
        "related": ["python", "functions"]
    },
    "inheritance": {
        "id": "inheritance",
        "name": "Inheritance in OOP",
        "description": "Creating class hierarchies in Python",
        "prerequisites": ["oop"],
        "related": ["python", "oop"]
    },
    "polymorphism": {
        "id": "polymorphism",
        "name": "Polymorphism in OOP",
        "description": "Multiple forms of methods in Python",
        "prerequisites": ["oop"],
        "related": ["python", "oop"]
    },
    "algorithms": {
        "id": "algorithms",
        "name": "Basic Algorithms",
        "description": "Common algorithms in Python",
        "prerequisites": ["data_structures"],
        "related": ["python", "data_structures"]
    }
}

@api_app.get("/api/concept_graph")
async def api_get_concept_graph(concept_id: str = None):
    """API endpoint to get concept graph data for a specific concept or all concepts"""
    if concept_id:
        concept = CONCEPT_GRAPH.get(concept_id)
        if not concept:
            return JSONResponse(
                status_code=404,
                content={"error": f"Concept {concept_id} not found"}
            )
        return JSONResponse(content=concept)
    return JSONResponse(content={"concepts": list(CONCEPT_GRAPH.values())})

@mcp.tool()
async def get_concept(concept_id: str = None) -> Dict[str, Any]:
    """MCP tool to get a specific concept or all concepts"""
    if concept_id:
        concept = CONCEPT_GRAPH.get(concept_id)
        if not concept:
            return {"error": f"Concept {concept_id} not found"}
        return {"concept": concept}
    return {"concepts": list(CONCEPT_GRAPH.values())}

@mcp.tool()
async def assess_skill(student_id: str, concept_id: str) -> Dict[str, Any]:
    """Assess a student's understanding of a specific concept"""
    # Check if concept exists in our concept graph
    concept_data = await get_concept(concept_id)
    if isinstance(concept_data, dict) and "error" in concept_data:
        return {"error": f"Cannot assess skill: {concept_data['error']}"}
    
    # Get concept name, handling both direct dict and concept graph response
    if isinstance(concept_data, dict) and "concept" in concept_data:
        concept_name = concept_data["concept"].get("name", concept_id)
    elif isinstance(concept_data, dict) and "name" in concept_data:
        concept_name = concept_data["name"]
    else:
        concept_name = concept_id
        
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
        feedback["areas_for_improvement"].append("Needs to review fundamental concepts")
    elif score > 0.8:
        feedback["strengths"].append(f"Excellent grasp of {concept_name} concepts")
        feedback["recommendations"].append("Try more advanced problems")
    
    # Create assessment response
    assessment = {
        "student_id": student_id,
        "concept_id": concept_id,
        "concept_name": concept_name,
        "score": round(score, 2),  # Round to 2 decimal places
        "timestamp": timestamp,
        "feedback": feedback
    }
    return assessment

@mcp.resource("concept-graph://")
async def get_concept_graph_resource() -> Dict[str, Any]:
    """Get the full knowledge concept graph"""
    return {
        "nodes": [
            {"id": "python", "name": "Python Basics", "difficulty": 1, "type": "foundation"},
            {"id": "functions", "name": "Functions", "difficulty": 2, "type": "concept"},
            {"id": "oop", "name": "OOP in Python", "difficulty": 3, "type": "paradigm"},
            {"id": "data_structures", "name": "Data Structures", "difficulty": 2, "type": "concept"},
            {"id": "decorators", "name": "Decorators", "difficulty": 4, "type": "advanced"},
            {"id": "lambdas", "name": "Lambda Functions", "difficulty": 2, "type": "concept"},
            {"id": "inheritance", "name": "Inheritance", "difficulty": 3, "type": "oop"},
            {"id": "polymorphism", "name": "Polymorphism", "difficulty": 3, "type": "oop"},
            {"id": "algorithms", "name": "Algorithms", "difficulty": 3, "type": "concept"}
        ],
        "edges": [
            {"from": "python", "to": "functions", "weight": 0.9},
            {"from": "python", "to": "oop", "weight": 0.8},
            {"from": "python", "to": "data_structures", "weight": 0.9},
            {"from": "functions", "to": "decorators", "weight": 0.8},
            {"from": "functions", "to": "lambdas", "weight": 0.7},
            {"from": "oop", "to": "inheritance", "weight": 0.9},
            {"from": "oop", "to": "polymorphism", "weight": 0.8},
            {"from": "data_structures", "to": "algorithms", "weight": 0.9}
        ]
    }

@mcp.resource("learning-path://{student_id}")
async def get_learning_path(student_id: str) -> Dict[str, Any]:
    """Get personalized learning path for a student"""
    return {
        "student_id": student_id,
        "current_concepts": ["math_algebra_linear_equations"]
    }

# Lesson Generation
@mcp.tool()
async def generate_lesson(topic: str, grade_level: int, duration_minutes: int) -> Dict[str, Any]:
    """
    Generate a lesson plan for the given topic, grade level, and duration
    
    Args:
        topic: The topic for the lesson
        grade_level: The grade level (1-12)
        duration_minutes: Duration of the lesson in minutes
        
    Returns:
        Dictionary containing the generated lesson plan
    """
    # In a real implementation, this would generate a lesson plan using an LLM
    # For now, we'll return a mock lesson plan
    return {
        "lesson_id": f"lesson_{int(datetime.utcnow().timestamp())}",
        "topic": topic,
        "grade_level": grade_level,
        "duration_minutes": duration_minutes,
        "objectives": [
            f"Understand the key concepts of {topic}",
            f"Apply {topic} to solve problems",
            f"Analyze examples of {topic} in real-world contexts"
        ],
        "materials": ["Whiteboard", "Markers", "Printed worksheets"],
        "activities": [
            {
                "name": "Introduction",
                "duration": 5,
                "description": f"Brief introduction to {topic} and its importance"
            },
            {
                "name": "Direct Instruction",
                "duration": 15,
                "description": f"Explain the main concepts of {topic} with examples"
            },
            {
                "name": "Guided Practice",
                "duration": 15,
                "description": "Work through example problems together"
            },
            {
                "name": "Independent Practice",
                "duration": 10,
                "description": "Students work on problems independently"
            }
        ],
        "assessment": {
            "type": "formative",
            "description": "Exit ticket with 2-3 problems related to the lesson"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# Assessment Suite
@mcp.tool()
async def generate_quiz(concept_ids: List[str], difficulty: int = 2) -> Dict[str, Any]:
    """
    Generate a quiz based on specified concepts and difficulty
    
    Args:
        concept_ids: List of concept IDs to include in the quiz
        difficulty: Difficulty level from 1-5
        
    Returns:
        Quiz object with questions and answers
    """
    # In a real implementation, this would generate questions based on the concepts
    # For now, we'll return a mock quiz
    questions = []
    for i, concept_id in enumerate(concept_ids[:5]):  # Limit to 5 questions max
        concept = CONCEPT_GRAPH.get(concept_id, {"name": f"Concept {concept_id}"})
        questions.append({
            "id": f"q{i+1}",
            "concept_id": concept_id,
            "concept_name": concept.get("name", f"Concept {concept_id}"),
            "question": f"Sample question about {concept.get('name', concept_id)}?",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "correct_answer": random.randint(0, 3),  # Random correct answer index
            "difficulty": min(max(1, difficulty), 5),  # Clamp difficulty between 1-5
            "explanation": f"This is an explanation for the question about {concept.get('name', concept_id)}"
        })
    
    return {
        "quiz_id": f"quiz_{int(datetime.utcnow().timestamp())}",
        "concept_ids": concept_ids,
        "difficulty": difficulty,
        "questions": questions,
        "timestamp": datetime.utcnow().isoformat()
    }



# API Endpoints
@api_app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@api_app.get("/api/assess_skill")
async def assess_skill_api(
    request: Request,
    student_id: Optional[str] = Query(None, description="Student ID"),
    concept_id: Optional[str] = Query(None, description="Concept ID to assess")
):
    """
    Assess a student's understanding of a specific concept
    
    Args:
        student_id: Student's unique identifier
        concept_id: Concept ID to assess
        
    Returns:
        Assessment results with score and feedback
    """
    try:
        # Get query parameters
        params = dict(request.query_params)
        
        # Check for required parameters
        if not student_id or not concept_id:
            raise HTTPException(
                status_code=400,
                detail="Both student_id and concept_id are required parameters"
            )
        
        # Call the assess_skill function
        result = await assess_skill(student_id, concept_id)
        
        # Handle error responses
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
            
        return result
        
    except HTTPException as http_err:
        # Re-raise HTTP exceptions as is
        raise http_err
    except Exception as e:
        # Log the error for debugging
        print(f"Error in assess_skill_api: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return a user-friendly error message
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )

@api_app.post("/api/generate_lesson")
async def generate_lesson_api(request: Dict[str, Any]):
    """
    Generate a lesson plan based on the provided parameters
    
    Expected request format:
    {
        "topic": "Lesson Topic",
        "grade_level": 9,  # 1-12
        "duration_minutes": 45
    }
    """
    try:
        # Validate request
        if not isinstance(request, dict):
            raise HTTPException(
                status_code=400,
                detail="Request must be a JSON object"
            )
            
        # Get parameters with validation
        topic = request.get("topic")
        if not topic or not isinstance(topic, str):
            raise HTTPException(
                status_code=400,
                detail="Topic is required and must be a string"
            )
            
        grade_level = request.get("grade_level")
        if not isinstance(grade_level, int) or not (1 <= grade_level <= 12):
            raise HTTPException(
                status_code=400,
                detail="Grade level must be an integer between 1 and 12"
            )
            
        duration_minutes = request.get("duration_minutes")
        if not isinstance(duration_minutes, (int, float)) or duration_minutes <= 0:
            raise HTTPException(
                status_code=400,
                detail="Duration must be a positive number"
            )
        
        # Generate the lesson plan
        result = await generate_lesson(topic, grade_level, int(duration_minutes))
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate lesson: {str(e)}")

@api_app.post("/api/generate_quiz")
async def generate_quiz_api(request: Dict[str, Any]):
    """
    Generate a quiz based on specified concepts and difficulty
    
    Expected request format:
    {
        "concept_ids": ["concept1", "concept2", ...],
        "difficulty": 2  # Optional, default is 2
    }
    """
    try:
        # Validate request
        if not isinstance(request, dict) or "concept_ids" not in request:
            raise HTTPException(
                status_code=400,
                detail="Request must be a JSON object with 'concept_ids' key"
            )
        
        # Get parameters with defaults
        concept_ids = request.get("concept_ids", [])
        difficulty = request.get("difficulty", 2)
        
        # Validate types
        if not isinstance(concept_ids, list):
            concept_ids = [concept_ids]  # Convert single concept to list
            
        if not all(isinstance(cid, str) for cid in concept_ids):
            raise HTTPException(
                status_code=400,
                detail="All concept IDs must be strings"
            )
            
        difficulty = int(difficulty)  # Ensure difficulty is an integer
        
        # Generate the quiz
        result = await generate_quiz(concept_ids, difficulty)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")

@mcp.tool()
async def get_curriculum_standards(country_code: str = "us") -> Dict[str, Any]:
    """
    Get curriculum standards for a specific country
    
    Args:
        country_code: ISO country code (e.g., 'us', 'uk')
        
    Returns:
        Dictionary containing curriculum standards
    """
    # Mock data - in a real implementation, this would come from a database or external API
    standards = {
        "us": {
            "name": "Common Core State Standards (US)",
            "subjects": {
                "math": {
                    "description": "Mathematics standards focusing on conceptual understanding, procedural skills, and problem solving",
                    "domains": ["Number & Operations", "Algebra", "Geometry", "Statistics & Probability"]
                },
                "ela": {
                    "description": "English Language Arts standards for reading, writing, speaking, and listening",
                    "domains": ["Reading", "Writing", "Speaking & Listening", "Language"]
                }
            },
            "grade_levels": list(range(1, 13)),
            "website": "http://www.corestandards.org"
        },
        "uk": {
            "name": "National Curriculum (UK)",
            "subjects": {
                "maths": {
                    "description": "Mathematics programme of study for key stages 1-4",
                    "domains": ["Number", "Algebra", "Ratio & Proportion", "Geometry", "Statistics"]
                },
                "english": {
                    "description": "English programme of study for key stages 1-4",
                    "domains": ["Reading", "Writing", "Grammar & Vocabulary", "Spoken English"]
                }
            },
            "key_stages": ["KS1 (5-7)", "KS2 (7-11)", "KS3 (11-14)", "KS4 (14-16)"],
            "website": "https://www.gov.uk/government/collections/national-curriculum"
        }
    }
    
    # Default to US standards if country not found
    country_code = country_code.lower()
    if country_code not in standards:
        country_code = "us"
    
    return {
        "country_code": country_code,
        "standards": standards[country_code],
        "timestamp": datetime.utcnow().isoformat()
    }

@api_app.get("/api/curriculum-standards")
async def get_curriculum_standards_api(country: str = "us"):
    """
    Get curriculum standards for a specific country
    
    Args:
        country: ISO country code (e.g., 'us', 'uk')
        
    Returns:
        Dictionary containing curriculum standards
    """
    try:
        # Validate country code
        if not isinstance(country, str) or len(country) != 2:
            raise HTTPException(
                status_code=400,
                detail="Country code must be a 2-letter ISO code"
            )
            
        # Get the standards
        result = await get_curriculum_standards(country)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch curriculum standards: {str(e)}"
        )

# Mount MCP app to /mcp path
mcp.app = api_app

def run_server():
    """Run the MCP server with configured transport and port"""
    print(f"Starting TutorX MCP Server on {SERVER_HOST}:{SERVER_PORT} using {SERVER_TRANSPORT} transport...")
    try:
        # Run the MCP server directly
        import uvicorn
        uvicorn.run(
            "main:mcp.app",
            host=SERVER_HOST,
            port=SERVER_PORT,
            log_level="info",
            reload=True
        )
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        raise

if __name__ == "__main__":
    run_server()