"""
Tests for the TutorX MCP client
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json
import requests

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client import TutorXClient


class TestTutorXClient(unittest.TestCase):
    """Test cases for the TutorX MCP client"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = TutorXClient("http://localhost:8000")
        self.student_id = "test_student_123"
        self.concept_id = "math_algebra_basics"
    
    @patch('client.requests.post')
    def test_call_tool(self, mock_post):
        """Test _call_tool method"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "success"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Call method
        result = self.client._call_tool("test_tool", {"param": "value"})
        
        # Assertions
        self.assertEqual(result, {"result": "success"})
        mock_post.assert_called_once_with(
            "http://localhost:8000/tools/test_tool",
            json={"param": "value"},
            headers={"Content-Type": "application/json"}
        )
        mock_response.raise_for_status.assert_called_once()
        
    @patch('client.requests.get')
    def test_get_resource(self, mock_get):
        """Test _get_resource method"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"resource": "data"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Call method
        result = self.client._get_resource("test-resource://identifier")
        
        # Assertions
        self.assertEqual(result, {"resource": "data"})
        mock_get.assert_called_once_with(
            "http://localhost:8000/resources?uri=test-resource://identifier",
            headers={"Accept": "application/json"}
        )
        mock_response.raise_for_status.assert_called_once()
        
    @patch('client.TutorXClient._call_tool')
    def test_assess_skill(self, mock_call_tool):
        """Test assess_skill method"""
        # Setup mock return value
        mock_call_tool.return_value = {"skill_level": 0.75}
        
        # Call method
        result = self.client.assess_skill(self.student_id, self.concept_id)
        
        # Assertions
        self.assertEqual(result, {"skill_level": 0.75})
        mock_call_tool.assert_called_once_with("assess_skill", {
            "student_id": self.student_id,
            "concept_id": self.concept_id
        })
        
    @patch('client.TutorXClient._get_resource')
    def test_get_concept_graph(self, mock_get_resource):
        """Test get_concept_graph method"""
        # Setup mock return value
        mock_get_resource.return_value = {"nodes": [], "edges": []}
        
        # Call method
        result = self.client.get_concept_graph()
        
        # Assertions
        self.assertEqual(result, {"nodes": [], "edges": []})
        mock_get_resource.assert_called_once_with("concept-graph://")
        
    @patch('client.TutorXClient._call_tool')
    def test_generate_quiz(self, mock_call_tool):
        """Test generate_quiz method"""
        # Setup mock return value
        mock_call_tool.return_value = {"questions": []}
        
        # Call method
        concept_ids = [self.concept_id]
        difficulty = 3
        result = self.client.generate_quiz(concept_ids, difficulty)
        
        # Assertions
        self.assertEqual(result, {"questions": []})
        mock_call_tool.assert_called_once_with("generate_quiz", {
            "concept_ids": concept_ids,
            "difficulty": difficulty
        })
        
    @patch('client.requests.post')
    def test_error_handling(self, mock_post):
        """Test error handling in _call_tool"""
        # Setup mock to raise exception
        mock_post.side_effect = requests.RequestException("Connection error")
        
        # Call method
        result = self.client._call_tool("test_tool", {})
        
        # Assertions
        self.assertIn("error", result)
        self.assertIn("Connection error", result["error"])
        self.assertIn("timestamp", result)


if __name__ == "__main__":
    unittest.main()
