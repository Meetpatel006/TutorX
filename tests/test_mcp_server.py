"""
Tests for the TutorX MCP server
"""

import sys
import os
import unittest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import assess_skill, generate_quiz, get_concept_graph


class TestMCPServer(unittest.TestCase):
    """Test cases for the TutorX MCP server"""

    def setUp(self):
        """Set up test fixtures"""
        self.student_id = "test_student_123"
        self.concept_id = "math_algebra_basics"
        
    def test_assess_skill(self):
        """Test assess_skill tool"""
        result = assess_skill(self.student_id, self.concept_id)
        
        # Verify the structure of the result
        self.assertIsInstance(result, dict)
        self.assertEqual(result["student_id"], self.student_id)
        self.assertEqual(result["concept_id"], self.concept_id)
        self.assertIsInstance(result["skill_level"], float)
        self.assertIsInstance(result["confidence"], float)
        self.assertIsInstance(result["recommendations"], list)
        self.assertIn("timestamp", result)
        
    def test_generate_quiz(self):
        """Test generate_quiz tool"""
        concept_ids = [self.concept_id]
        difficulty = 2
        
        result = generate_quiz(concept_ids, difficulty)
        
        # Verify the structure of the result
        self.assertIsInstance(result, dict)
        self.assertIn("quiz_id", result)
        self.assertEqual(result["concept_ids"], concept_ids)
        self.assertEqual(result["difficulty"], difficulty)
        self.assertIsInstance(result["questions"], list)
        self.assertGreater(len(result["questions"]), 0)
        
        # Check question structure
        question = result["questions"][0]
        self.assertIn("id", question)
        self.assertIn("text", question)
        self.assertIn("type", question)
        self.assertIn("answer", question)
        self.assertIn("solution_steps", question)
        
    def test_get_concept_graph(self):
        """Test get_concept_graph resource"""
        result = get_concept_graph()
        
        # Verify the structure of the result
        self.assertIsInstance(result, dict)
        self.assertIn("nodes", result)
        self.assertIn("edges", result)
        self.assertIsInstance(result["nodes"], list)
        self.assertIsInstance(result["edges"], list)
        self.assertGreater(len(result["nodes"]), 0)
        self.assertGreater(len(result["edges"]), 0)
        
        # Check node structure
        node = result["nodes"][0]
        self.assertIn("id", node)
        self.assertIn("name", node)
        self.assertIn("difficulty", node)
        
        # Check edge structure
        edge = result["edges"][0]
        self.assertIn("from", edge)
        self.assertIn("to", edge)
        self.assertIn("weight", edge)


if __name__ == "__main__":
    unittest.main()
