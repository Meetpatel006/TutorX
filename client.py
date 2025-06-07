"""
MCP client for interacting with the TutorX MCP server.
This module provides functions that interact with the MCP server
for use by the Gradio interface.
"""

import json
import requests
from typing import Dict, Any, List, Optional
import base64
from datetime import datetime

# Default MCP server URL
MCP_SERVER_URL = "http://localhost:8000"

class TutorXClient:
    """Client for interacting with the TutorX MCP server"""
    
    def __init__(self, server_url=MCP_SERVER_URL):
        self.server_url = server_url
    
    def _call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool on the server
        
        Args:
            tool_name: Name of the tool to call
            params: Parameters to pass to the tool
            
        Returns:
            Tool response
        """
        try:
            response = requests.post(
                f"{self.server_url}/tools/{tool_name}",
                json=params,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "error": f"Failed to call tool: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """
        Get an MCP resource from the server
        
        Args:
            resource_uri: URI of the resource to get
            
        Returns:
            Resource data
        """
        try:
            response = requests.get(
                f"{self.server_url}/resources?uri={resource_uri}",
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "error": f"Failed to get resource: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    # ------------ Core Features ------------
    
    def assess_skill(self, student_id: str, concept_id: str) -> Dict[str, Any]:
        """Assess student's skill level on a specific concept"""
        return self._call_tool("assess_skill", {
            "student_id": student_id,
            "concept_id": concept_id
        })
    
    def get_concept_graph(self) -> Dict[str, Any]:
        """Get the full knowledge concept graph"""
        return self._get_resource("concept-graph://")
    
    def get_learning_path(self, student_id: str) -> Dict[str, Any]:
        """Get personalized learning path for a student"""
        return self._get_resource(f"learning-path://{student_id}")
    
    def generate_quiz(self, concept_ids: List[str], difficulty: int = 2) -> Dict[str, Any]:
        """Generate a quiz based on specified concepts and difficulty"""
        return self._call_tool("generate_quiz", {
            "concept_ids": concept_ids,
            "difficulty": difficulty
        })
    
    def analyze_error_patterns(self, student_id: str, concept_id: str) -> Dict[str, Any]:
        """Analyze common error patterns for a student on a specific concept"""
        return self._call_tool("analyze_error_patterns", {
            "student_id": student_id,
            "concept_id": concept_id
        })
    
    # ------------ Advanced Features ------------
    
    def analyze_cognitive_state(self, eeg_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze EEG data to determine cognitive state"""
        return self._call_tool("analyze_cognitive_state", {
            "eeg_data": eeg_data
        })
    
    def get_curriculum_standards(self, country_code: str) -> Dict[str, Any]:
        """Get curriculum standards for a specific country"""
        return self._get_resource(f"curriculum-standards://{country_code}")
    
    def align_content_to_standard(self, content_id: str, standard_id: str) -> Dict[str, Any]:
        """Align educational content to a specific curriculum standard"""
        return self._call_tool("align_content_to_standard", {
            "content_id": content_id,
            "standard_id": standard_id
        })
    
    def generate_lesson(self, topic: str, grade_level: int, duration_minutes: int = 45) -> Dict[str, Any]:
        """Generate a complete lesson plan on a topic"""
        return self._call_tool("generate_lesson", {
            "topic": topic,
            "grade_level": grade_level,
            "duration_minutes": duration_minutes
        })
    
    # ------------ User Experience ------------
    
    def get_student_dashboard(self, student_id: str) -> Dict[str, Any]:
        """Get dashboard data for a specific student"""
        return self._get_resource(f"student-dashboard://{student_id}")
    
    def get_accessibility_settings(self, student_id: str) -> Dict[str, Any]:
        """Get accessibility settings for a student"""
        return self._call_tool("get_accessibility_settings", {
            "student_id": student_id
        })
    
    def update_accessibility_settings(self, student_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update accessibility settings for a student"""
        return self._call_tool("update_accessibility_settings", {
            "student_id": student_id,
            "settings": settings
        })
    
    # ------------ Multi-Modal Interaction ------------
    
    def text_interaction(self, query: str, student_id: str) -> Dict[str, Any]:
        """Process a text query from the student"""
        return self._call_tool("text_interaction", {
            "query": query,
            "student_id": student_id
        })
    
    def voice_interaction(self, audio_data_base64: str, student_id: str) -> Dict[str, Any]:
        """Process voice input from the student"""
        return self._call_tool("voice_interaction", {
            "audio_data_base64": audio_data_base64,
            "student_id": student_id
        })
    
    def handwriting_recognition(self, image_data_base64: str, student_id: str) -> Dict[str, Any]:
        """Process handwritten input from the student"""
        return self._call_tool("handwriting_recognition", {
            "image_data_base64": image_data_base64,
            "student_id": student_id
        })
    
    # ------------ Assessment ------------
    
    def create_assessment(self, concept_ids: List[str], num_questions: int, difficulty: int = 3) -> Dict[str, Any]:
        """Create a complete assessment for given concepts"""
        return self._call_tool("create_assessment", {
            "concept_ids": concept_ids,
            "num_questions": num_questions,
            "difficulty": difficulty
        })
    
    def grade_assessment(self, assessment_id: str, student_answers: Dict[str, str], questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Grade a completed assessment"""
        return self._call_tool("grade_assessment", {
            "assessment_id": assessment_id,
            "student_answers": student_answers,
            "questions": questions
        })
    
    def get_student_analytics(self, student_id: str, timeframe_days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics for a student"""
        return self._call_tool("get_student_analytics", {
            "student_id": student_id,
            "timeframe_days": timeframe_days
        })
      def check_submission_originality(self, submission: str, reference_sources: List[str]) -> Dict[str, Any]:
        """Check student submission for potential plagiarism"""
        return self._call_tool("check_submission_originality", {
            "submission": submission,
            "reference_sources": reference_sources
        })
    
    # ------------ External Integrations ------------
    
    def lms_sync_grades(self, lms_type: str, api_url: str, api_key: str, 
                      course_id: str, assignment_id: str, 
                      grades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync grades with a Learning Management System"""
        return self._call_tool("lms_sync_grades", {
            "lms_type": lms_type,
            "api_url": api_url,
            "api_key": api_key,
            "course_id": course_id,
            "assignment_id": assignment_id,
            "grades": grades
        })
    
    def oer_search(self, repository_url: str, query: str, 
                  subject: Optional[str] = None, grade_level: Optional[str] = None,
                  api_key: Optional[str] = None) -> Dict[str, Any]:
        """Search for educational resources in OER repositories"""
        params = {
            "repository_url": repository_url,
            "query": query
        }
        
        if subject:
            params["subject"] = subject
            
        if grade_level:
            params["grade_level"] = grade_level
            
        if api_key:
            params["api_key"] = api_key
            
        return self._call_tool("oer_search", params)
    
    def schedule_tutoring_session(self, platform_url: str, client_id: str, client_secret: str,
                                student_id: str, subject: str, datetime_str: str) -> Dict[str, Any]:
        """Schedule a session with a real-time personalized tutoring platform"""
        return self._call_tool("schedule_tutoring_session", {
            "platform_url": platform_url,
            "client_id": client_id,
            "client_secret": client_secret,
            "student_id": student_id,
            "subject": subject,
            "datetime_str": datetime_str
        })

# Create a default client instance for easy import
client = TutorXClient()
