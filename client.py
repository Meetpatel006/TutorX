"""
MCP client for interacting with the TutorX MCP server.
This module provides functions that interact with the MCP server
for use by the Gradio interface.
"""

import json
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
import base64
from datetime import datetime
import os

# Get server configuration from environment variables with defaults
DEFAULT_HOST = os.getenv("MCP_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("MCP_PORT", "8001"))  # Default port updated to 8001
DEFAULT_SERVER_URL = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"

# API endpoints
API_PREFIX = "/api"

class TutorXClient:
    """Client for interacting with the TutorX MCP server"""
    
    def __init__(self, server_url=DEFAULT_SERVER_URL):
        self.server_url = server_url
        self.session = None
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
    
    async def _call_tool(self, tool_name: str, params: Dict[str, Any], method: str = "POST") -> Dict[str, Any]:
        """
        Call an MCP tool on the server
        
        Args:
            tool_name: Name of the tool to call
            params: Parameters to pass to the tool
            method: HTTP method to use (GET or POST)
            
        Returns:
            Tool response
        """
        await self._ensure_session()
        try:
            url = f"{self.server_url}{API_PREFIX}/{tool_name}"
            
            # Convert params to query string for GET requests
            if method.upper() == "GET":
                from urllib.parse import urlencode
                if params:
                    query_string = urlencode(params, doseq=True)
                    url = f"{url}?{query_string}"
                async with self.session.get(url, timeout=30) as response:
                    return await self._handle_response(response)
            else:
                async with self.session.post(url, json=params, timeout=30) as response:
                    return await self._handle_response(response)
                    
        except Exception as e:
            return {
                "error": f"Failed to call tool: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_response(self, response) -> Dict[str, Any]:
        """Handle the HTTP response"""
        if response.status == 200:
            return await response.json()
        else:
            error = await response.text()
            return {
                "error": f"API error ({response.status}): {error}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """
        Get an MCP resource from the server
        
        Args:
            resource_uri: URI of the resource to get
            
        Returns:
            Resource data
        """
        await self._ensure_session()
        try:
            # Extract the resource name from the URI (e.g., 'concept-graph' from 'concept-graph://')
            resource_name = resource_uri.split('://')[0]
            url = f"{self.server_url}{API_PREFIX}/{resource_name}"
            
            async with self.session.get(url, timeout=30) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    return {
                        "error": f"Failed to get resource: {error}",
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "error": f"Failed to get resource: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_server_connection(self) -> bool:
        """
        Check if the server is accessible
        
        Returns:
            bool: True if server is accessible, False otherwise
        """
        await self._ensure_session()
        try:
            async with self.session.get(
                f"{self.server_url}{API_PREFIX}/health",
                timeout=5
            ) as response:
                return response.status == 200
        except Exception as e:
            print(f"Server connection check failed: {str(e)}")
            return False
    
    # ------------ Core Features ------------
    
    async def get_concept_graph(self, concept_id: str = None, use_mcp: bool = False) -> Dict[str, Any]:
        """
        Get the concept graph for a specific concept or all concepts.
        
        Args:
            concept_id: Optional ID of the concept to fetch. If None, returns all concepts.
            use_mcp: If True, uses the MCP tool interface instead of direct API call.
            
        Returns:
            Dict containing concept data or error information.
        """
        try:
            # Ensure we have a session
            await self._ensure_session()
            
            if use_mcp:
                # Use MCP tool interface
                print(f"[CLIENT] Using MCP tool to get concept graph for: {concept_id}")
                return await self._call_tool("get_concept_graph", {"concept_id": concept_id} if concept_id else {})
            
            # Use direct API call (default)
            url = f"{self.server_url}/api/concept_graph"
            params = {}
            if concept_id:
                params["concept_id"] = concept_id
            
            print(f"[CLIENT] Fetching concept graph from {url} with params: {params}")
            
            async with self.session.get(
                url,
                params=params,
                timeout=30
            ) as response:
                print(f"[CLIENT] Response status: {response.status}")
                
                if response.status == 404:
                    error_msg = f"Concept {concept_id} not found"
                    print(f"[CLIENT] {error_msg}")
                    return {"error": error_msg}
                    
                response.raise_for_status()
                
                # Parse the JSON response
                result = await response.json()
                print(f"[CLIENT] Received response: {result}")
                
                return result
                
        except asyncio.TimeoutError:
            error_msg = "Request timed out"
            print(f"[CLIENT] {error_msg}")
            return {"error": error_msg}
            
        except aiohttp.ClientError as e:
            error_msg = f"HTTP client error: {str(e)}"
            print(f"[CLIENT] {error_msg}")
            return {"error": error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"[CLIENT] {error_msg}")
            import traceback
            traceback.print_exc()
            return {"error": error_msg}
        
    async def assess_skill(self, student_id: str, concept_id: str) -> Dict[str, Any]:
        """Assess a student's skill on a specific concept"""
        return await self._call_tool("assess_skill", {"student_id": student_id, "concept_id": concept_id})
    
    async def get_learning_path(self, student_id: str) -> Dict[str, Any]:
        """Get personalized learning path for a student"""
        return await self._get_resource(f"learning-path://{student_id}")
    
    async def generate_quiz(self, concept_ids: List[str], difficulty: int = 2) -> Dict[str, Any]:
        """Generate a quiz based on specified concepts and difficulty"""
        return await self._call_tool("generate_quiz", {
            "concept_ids": concept_ids,
            "difficulty": difficulty
        })
    
    async def analyze_error_patterns(self, student_id: str, concept_id: str) -> Dict[str, Any]:
        """Analyze common error patterns for a student on a specific concept"""
        return await self._call_tool("analyze_error_patterns", {
            "student_id": student_id,
            "concept_id": concept_id
        })
    
    # ------------ Advanced Features ------------
    
    async def analyze_cognitive_state(self, eeg_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze EEG data to determine cognitive state"""
        return await self._call_tool("analyze_cognitive_state", {
            "eeg_data": eeg_data
        })
    
    async def get_curriculum_standards(self, country_code: str) -> Dict[str, Any]:
        """Get curriculum standards for a specific country"""
        return await self._get_resource(f"curriculum-standards://{country_code}")
    
    async def align_content_to_standard(self, content_id: str, standard_id: str) -> Dict[str, Any]:
        """Align educational content to a specific curriculum standard"""
        return await self._call_tool("align_content_to_standard", {
            "content_id": content_id,
            "standard_id": standard_id
        })
    
    async def generate_lesson(self, topic: str, grade_level: int, duration_minutes: int = 45) -> Dict[str, Any]:
        """Generate a complete lesson plan on a topic"""
        return await self._call_tool("generate_lesson", {
            "topic": topic,
            "grade_level": grade_level,
            "duration_minutes": duration_minutes
        })
    
    # ------------ User Experience ------------
    
    async def get_student_dashboard(self, student_id: str) -> Dict[str, Any]:
        """Get dashboard data for a specific student"""
        return await self._get_resource(f"student-dashboard://{student_id}")
    
    async def get_accessibility_settings(self, student_id: str) -> Dict[str, Any]:
        """Get accessibility settings for a student"""
        return await self._call_tool("get_accessibility_settings", {
            "student_id": student_id
        })
    
    async def update_accessibility_settings(self, student_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update accessibility settings for a student"""
        return await self._call_tool("update_accessibility_settings", {
            "student_id": student_id,
            "settings": settings
        })
    
    # ------------ Multi-Modal Interaction ------------
    
    async def text_interaction(self, query: str, student_id: str) -> Dict[str, Any]:
        """Process a text query from the student"""
        return await self._call_tool("text_interaction", {
            "query": query,
            "student_id": student_id
        })
    
    async def voice_interaction(self, audio_data_base64: str, student_id: str) -> Dict[str, Any]:
        """Process voice input from the student"""
        return await self._call_tool("voice_interaction", {
            "audio_data_base64": audio_data_base64,
            "student_id": student_id
        })
    
    async def handwriting_recognition(self, image_data_base64: str, student_id: str) -> Dict[str, Any]:
        """Process handwritten input from the student"""
        return await self._call_tool("handwriting_recognition", {
            "image_data_base64": image_data_base64,
            "student_id": student_id
        })
    
    # ------------ Assessment ------------
    
    async def create_assessment(self, concept_ids: List[str], num_questions: int, difficulty: int = 3) -> Dict[str, Any]:
        """Create a complete assessment for given concepts"""
        return await self._call_tool("create_assessment", {
            "concept_ids": concept_ids,
            "num_questions": num_questions,
            "difficulty": difficulty
        })
    
    async def grade_assessment(self, assessment_id: str, student_answers: Dict[str, str], questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Grade a completed assessment"""
        return await self._call_tool("grade_assessment", {
            "assessment_id": assessment_id,
            "student_answers": student_answers,
            "questions": questions
        })
    
    async def get_student_analytics(self, student_id: str, timeframe_days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics for a student"""
        return await self._call_tool("get_student_analytics", {
            "student_id": student_id,
            "timeframe_days": timeframe_days
        })
    
    async def check_submission_originality(self, submission: str, reference_sources: List[str]) -> Dict[str, Any]:
        """Check student submission for potential plagiarism"""
        return await self._call_tool("check_submission_originality", {
            "submission": submission,
            "reference_sources": reference_sources
        })
    

    async def get_curriculum_standards(self, country_code: str = "us") -> Dict[str, Any]:
        """
        Get curriculum standards for a specific country
        
        Args:
            country_code: ISO country code (e.g., 'us', 'uk')
            
        Returns:
            Dictionary containing curriculum standards
        """
        return await self._call_tool(
            "curriculum-standards",  # Note the endpoint name matches the API route
            {"country": country_code.lower()},  # Note the parameter name matches the API
            method="GET"  # Use GET for this endpoint
        )
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def generate_lesson(self, topic: str, grade_level: int, duration_minutes: int) -> Dict[str, Any]:
        """
        Generate a lesson plan for the given topic, grade level, and duration
        
        Args:
            topic: The topic for the lesson
            grade_level: The grade level (1-12)
            duration_minutes: Duration of the lesson in minutes
            
        Returns:
            Dictionary containing the generated lesson plan
        """
        return await self._call_tool(
            "generate_lesson",
            {
                "topic": topic,
                "grade_level": grade_level,
                "duration_minutes": duration_minutes
            }
        )

# Create a default client instance for easy import
client = TutorXClient()
