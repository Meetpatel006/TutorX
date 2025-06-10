"""
Concept graph tools for TutorX MCP.
"""
from typing import Dict, Any, Optional
import sys
import os
from pathlib import Path
import json
import re

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


USER_PROMPT_TEMPLATE = """You are an expert educational content creator and knowledge graph expert that helps create detailed concept graphs for educational purposes.
Your task is to generate a comprehensive concept graph for a given topic, including related concepts and prerequisites.

IMPORTANT: Output only valid JSON. Do not include any explanatory text before or after the JSON. Do not include comments. Do not include trailing commas. Double-check that your output is valid JSON and can be parsed by Python's json.loads().

Output Format (JSON):
{{
  "concepts": [
    {{
      "id": "unique_concept_identifier",
      "name": "Concept Name",
      "description": "Clear and concise description of the concept",
      "related_concepts": [
        {{
          "id": "related_concept_id",
          "name": "Related Concept Name",
          "description": "Brief description of the relationship"
        }}
      ],
      "prerequisites": [
        {{
          "id": "prerequisite_id",
          "name": "Prerequisite Concept Name",
          "description": "Why this is a prerequisite"
        }}
      ]
    }}
  ]
}}

Guidelines:
1. Keep concept IDs lowercase with underscores (snake_case)
2. Include 1 related concepts and 1 prerequisites per concept
3. Ensure descriptions are educational and concise
4. Maintain consistency in the knowledge domain
5. Include fundamental concepts even if not directly mentioned

Generate a detailed concept graph for: {concept}

Focus on {domain} concepts and provide a comprehensive graph with related concepts and prerequisites.
Include both broad and specific concepts relevant to this topic.

Remember: Return only valid JSON, no additional text. Do not include trailing commas. Do not include comments. Double-check your output is valid JSON."""

# Sample concept graph as fallback
SAMPLE_CONCEPT_GRAPH = {
    "concepts": [
        {
            "id": "machine_learning",
            "name": "Machine Learning",
            "description": "A branch of artificial intelligence that focuses on algorithms that can learn from and make predictions on data",
            "related_concepts": [
                {
                    "id": "artificial_intelligence",
                    "name": "Artificial Intelligence",
                    "description": "The broader field that encompasses machine learning"
                },
                {
                    "id": "deep_learning",
                    "name": "Deep Learning",
                    "description": "A subset of machine learning using neural networks"
                }
            ],
            "prerequisites": [
                {
                    "id": "statistics",
                    "name": "Statistics",
                    "description": "Understanding of statistical concepts is fundamental"
                }
            ]
        }
    ]
}

def clean_json_trailing_commas(json_text: str) -> str:
    # Remove trailing commas before } or ]
    return re.sub(r',([ \t\r\n]*[}}\]])', r'\1', json_text)

def extract_json_from_text(text: str) -> Optional[dict]:
    if not text or not isinstance(text, str):
        return None

    try:
        # Remove all code fences (``` or ```json) at the start/end, with optional whitespace
        text = re.sub(r'^\s*```(?:json)?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*```\s*$', '', text, flags=re.IGNORECASE)
        text = text.strip()

        print(f"[DEBUG] LLM output ends with: {text[-500:]}")

        # Remove trailing commas
        cleaned = clean_json_trailing_commas(text)

        # Parse JSON
        return json.loads(cleaned)
    except Exception as e:
        print(f"[DEBUG] Failed JSON extraction: {e}")
        return None


async def generate_text(prompt: str, temperature: float = 0.7):
    """Generate text using the configured model."""
    try:
        print(f"[DEBUG] Calling MODEL.generate_text with prompt length: {len(prompt)}")
        print(f"[DEBUG] MODEL type: {type(MODEL)}")
        
        # Check if the model has the expected method
        if not hasattr(MODEL, 'generate_text'):
            print(f"[DEBUG] MODEL does not have generate_text method. Available methods: {dir(MODEL)}")
            raise AttributeError("MODEL does not have generate_text method")
        
        # This should call your actual model generation method
        # Adjust this based on your GeminiFlash implementation
        response = await MODEL.generate_text(
            prompt=prompt,
            temperature=temperature
        )
        return response
    except Exception as e:
        print(f"[DEBUG] Error in generate_text: {e}")
        print(f"[DEBUG] Error type: {type(e)}")
        raise


@mcp.tool()
async def get_concept_graph_tool(concept_id: Optional[str] = None, domain: str = "computer science") -> dict:
    """
    Generate or retrieve a concept graph for a given concept ID or name.
    
    Args:
        concept_id: The ID or name of the concept to retrieve
        domain: The knowledge domain (e.g., 'computer science', 'mathematics')
    
    Returns:
        dict: A single concept dictionary with keys: id, name, description, related_concepts, prerequisites
    """
    print(f"[DEBUG] get_concept_graph_tool called with concept_id: {concept_id}, domain: {domain}")
    
    if not concept_id:
        print(f"[DEBUG] No concept_id provided, returning sample concept")
        return SAMPLE_CONCEPT_GRAPH["concepts"][0]
    
    # Create a fallback custom concept based on the requested concept_id
    fallback_concept = {
        "id": concept_id.lower().replace(" ", "_"),
        "name": concept_id.title(),
        "description": f"A {domain} concept related to {concept_id}",
        "related_concepts": [
            {
                "id": "related_concept_1",
                "name": "Related Concept 1",
                "description": f"A concept related to {concept_id}"
            },
            {
                "id": "related_concept_2", 
                "name": "Related Concept 2",
                "description": f"Another concept related to {concept_id}"
            }
        ],
        "prerequisites": [
            {
                "id": "basic_prerequisite",
                "name": "Basic Prerequisite",
                "description": f"Basic knowledge required for understanding {concept_id}"
            }
        ]
    }
    
    # Try LLM generation first, fallback to custom concept if it fails
    try:
        print(f"[DEBUG] Attempting LLM generation for: {concept_id} in domain: {domain}")
        
        # Generate the concept graph using LLM
        prompt = USER_PROMPT_TEMPLATE.format(concept=concept_id, domain=domain)
        print(f"[DEBUG] Prompt created, length: {len(prompt)}")
        
        try:
            # Call the LLM to generate the concept graph
            print(f"[DEBUG] About to call generate_text...")
            response = await generate_text(
                prompt=prompt,
                temperature=0.7
            )
            print(f"[DEBUG] generate_text completed successfully")
            
        except Exception as gen_error:
            print(f"[DEBUG] Error in generate_text call: {gen_error}")
            print(f"[DEBUG] Returning fallback concept due to generation error")
            return fallback_concept
        
        # Handle different response formats
        response_text = None
        try:
            if hasattr(response, 'content'):
                if isinstance(response.content, list) and response.content:
                    if hasattr(response.content[0], 'text'):
                        response_text = response.content[0].text
                    else:
                        response_text = str(response.content[0])
                elif isinstance(response.content, str):
                    response_text = response.content
            elif hasattr(response, 'text'):
                response_text = response.text
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)
                
            print(f"[DEBUG] Extracted response_text type: {type(response_text)}")
            print(f"[DEBUG] Response text length: {len(response_text) if response_text else 0}")
            
        except Exception as extract_error:
            print(f"[DEBUG] Error extracting response text: {extract_error}")
            print(f"[DEBUG] Returning fallback concept due to extraction error")
            return fallback_concept
        
        if not response_text:
            print(f"[DEBUG] LLM response is empty, returning fallback concept")
            return fallback_concept
        
        try:
            result = extract_json_from_text(response_text)
            print(f"[DEBUG] JSON extraction result: {result is not None}")
            if result:
                print(f"[DEBUG] Extracted JSON keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        except Exception as json_error:
            print(f"[DEBUG] Error in extract_json_from_text: {json_error}")
            print(f"[DEBUG] Returning fallback concept due to JSON extraction error")
            return fallback_concept
        
        if not result:
            print(f"[DEBUG] No valid JSON extracted, returning fallback concept")
            return fallback_concept
        
        if "concepts" in result and isinstance(result["concepts"], list) and result["concepts"]:
            print(f"[DEBUG] Found {len(result['concepts'])} concepts in LLM response")
            # Find the requested concept or return the first
            for concept in result["concepts"]:
                if (concept.get("id") == concept_id or 
                    concept.get("name", "").lower() == concept_id.lower()):
                    print(f"[DEBUG] Found matching LLM concept: {concept.get('name')}")
                    return concept
            # If not found, return the first concept
            first_concept = result["concepts"][0]
            print(f"[DEBUG] Concept not found, returning first LLM concept: {first_concept.get('name')}")
            return first_concept
        else:
            print(f"[DEBUG] LLM JSON does not contain valid 'concepts' list, returning fallback")
            return fallback_concept
        
    except Exception as e:
        import traceback
        error_msg = f"Error generating concept graph: {str(e)}"
        print(f"[DEBUG] Exception in get_concept_graph_tool: {error_msg}")
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        # Return fallback concept instead of error
        print(f"[DEBUG] Returning fallback concept due to exception")
        return fallback_concept