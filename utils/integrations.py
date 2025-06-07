"""
Integration utilities for connecting TutorX-MCP with external educational systems
"""

import requests
import json
import os
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class LMSIntegration:
    """Integration with Learning Management Systems (Canvas, Moodle, etc.)"""
    
    def __init__(self, lms_type: str, api_url: str, api_key: str):
        """
        Initialize LMS integration
        
        Args:
            lms_type: Type of LMS ('canvas', 'moodle', 'blackboard', etc.)
            api_url: Base URL for LMS API
            api_key: API key or token for authentication
        """
        self.lms_type = lms_type.lower()
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        
    def get_courses(self) -> List[Dict[str, Any]]:
        """Get list of courses from LMS"""
        if self.lms_type == 'canvas':
            return self._canvas_get_courses()
        elif self.lms_type == 'moodle':
            return self._moodle_get_courses()
        else:
            raise ValueError(f"Unsupported LMS type: {self.lms_type}")
            
    def _canvas_get_courses(self) -> List[Dict[str, Any]]:
        """Get courses from Canvas LMS"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(f"{self.api_url}/courses", headers=headers)
        response.raise_for_status()
        return response.json()
        
    def _moodle_get_courses(self) -> List[Dict[str, Any]]:
        """Get courses from Moodle"""
        params = {
            "wstoken": self.api_key,
            "wsfunction": "core_course_get_courses",
            "moodlewsrestformat": "json"
        }
        response = requests.get(f"{self.api_url}/webservice/rest/server.php", params=params)
        response.raise_for_status()
        return response.json()
        
    def sync_grades(self, course_id: str, assignment_id: str, grades: List[Dict[str, Any]]) -> bool:
        """
        Sync grades to LMS
        
        Args:
            course_id: ID of the course
            assignment_id: ID of the assignment
            grades: List of grade data to sync
            
        Returns:
            Success status
        """
        try:
            if self.lms_type == 'canvas':
                return self._canvas_sync_grades(course_id, assignment_id, grades)
            elif self.lms_type == 'moodle':
                return self._moodle_sync_grades(course_id, assignment_id, grades)
            else:
                raise ValueError(f"Unsupported LMS type: {self.lms_type}")
        except Exception as e:
            logger.error(f"Error syncing grades: {e}")
            return False
            
    def _canvas_sync_grades(self, course_id: str, assignment_id: str, grades: List[Dict[str, Any]]) -> bool:
        """Sync grades to Canvas LMS"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        for grade in grades:
            data = {
                "submission": {
                    "posted_grade": grade["score"]
                }
            }
            
            url = f"{self.api_url}/courses/{course_id}/assignments/{assignment_id}/submissions/{grade['student_id']}"
            response = requests.put(url, json=data, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to sync grade for student {grade['student_id']}: {response.text}")
                return False
                
        return True
        
    def _moodle_sync_grades(self, course_id: str, assignment_id: str, grades: List[Dict[str, Any]]) -> bool:
        """Sync grades to Moodle"""
        # Implementation specific to Moodle's API
        # This would use the Moodle grade update API
        return True  # Placeholder
        
class OERIntegration:
    """Integration with Open Educational Resources repositories"""
    
    def __init__(self, repository_url: str, api_key: Optional[str] = None):
        """
        Initialize OER repository integration
        
        Args:
            repository_url: Base URL for OER repository API
            api_key: Optional API key if required by the repository
        """
        self.repository_url = repository_url.rstrip('/')
        self.api_key = api_key
        
    def search_resources(self, query: str, subject: Optional[str] = None, 
                        grade_level: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for educational resources
        
        Args:
            query: Search query
            subject: Optional subject filter
            grade_level: Optional grade level filter
            
        Returns:
            List of matching resources
        """
        params = {"q": query}
        
        if subject:
            params["subject"] = subject
            
        if grade_level:
            params["grade"] = grade_level
            
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        response = requests.get(f"{self.repository_url}/search", params=params, headers=headers)
        response.raise_for_status()
        
        return response.json().get("results", [])
        
    def get_resource(self, resource_id: str) -> Dict[str, Any]:
        """
        Get details for a specific resource
        
        Args:
            resource_id: ID of the resource to fetch
            
        Returns:
            Resource details
        """
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        response = requests.get(f"{self.repository_url}/resources/{resource_id}", headers=headers)
        response.raise_for_status()
        
        return response.json()
        

class RTPTIntegration:
    """Integration with real-time personalized tutoring platforms"""
    
    def __init__(self, platform_url: str, client_id: str, client_secret: str):
        """
        Initialize RTPT integration
        
        Args:
            platform_url: Base URL for RTPT platform API
            client_id: OAuth client ID
            client_secret: OAuth client secret
        """
        self.platform_url = platform_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = None
        
    def _get_access_token(self) -> str:
        """Get OAuth access token"""
        if self._access_token:
            return self._access_token
            
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = requests.post(f"{self.platform_url}/oauth/token", data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self._access_token = token_data["access_token"]
        return self._access_token
        
    def get_available_tutors(self, subject: str, level: str) -> List[Dict[str, Any]]:
        """
        Get available tutors for a subject and level
        
        Args:
            subject: Academic subject
            level: Academic level
            
        Returns:
            List of available tutors
        """
        headers = {"Authorization": f"Bearer {self._get_access_token()}"}
        params = {
            "subject": subject,
            "level": level
        }
        
        response = requests.get(f"{self.platform_url}/tutors/available", params=params, headers=headers)
        response.raise_for_status()
        
        return response.json()
        
    def schedule_session(self, student_id: str, tutor_id: str, 
                        subject: str, datetime_str: str) -> Dict[str, Any]:
        """
        Schedule a tutoring session
        
        Args:
            student_id: ID of the student
            tutor_id: ID of the tutor
            subject: Subject for tutoring
            datetime_str: ISO format datetime for the session
            
        Returns:
            Session details
        """
        headers = {"Authorization": f"Bearer {self._get_access_token()}"}
        data = {
            "student_id": student_id,
            "tutor_id": tutor_id,
            "subject": subject,
            "datetime": datetime_str
        }
        
        response = requests.post(f"{self.platform_url}/sessions", json=data, headers=headers)
        response.raise_for_status()
        
        return response.json()
