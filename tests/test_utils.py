"""
Tests for TutorX MCP utility functions
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.multimodal import process_text_query, process_voice_input, process_handwriting
from utils.assessment import generate_question, evaluate_student_answer


class TestMultimodalUtils(unittest.TestCase):
    """Test cases for multimodal utility functions"""
    
    def test_process_text_query(self):
        """Test text query processing"""
        # Test with a "solve" query
        solve_query = "Please solve this equation: 2x + 3 = 7"
        result = process_text_query(solve_query)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["query"], solve_query)
        self.assertEqual(result["response_type"], "math_solution")
        self.assertIn("response", result)
        self.assertIn("confidence", result)
        self.assertIn("timestamp", result)
        
        # Test with "what is" query
        what_is_query = "What is a quadratic equation?"
        result = process_text_query(what_is_query)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["query"], what_is_query)
        self.assertEqual(result["response_type"], "definition")
        self.assertIn("response", result)
        
        # Test with unknown query
        unknown_query = "Something completely different"
        result = process_text_query(unknown_query)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["query"], unknown_query)
        self.assertEqual(result["response_type"], "general")
        self.assertIn("response", result)
        
    def test_process_voice_input(self):
        """Test voice input processing"""
        mock_audio_data = "bW9jayBhdWRpbyBkYXRh"  # Base64 for "mock audio data"
        
        result = process_voice_input(mock_audio_data)
        
        self.assertIsInstance(result, dict)
        self.assertIn("transcription", result)
        self.assertIn("confidence", result)
        self.assertIn("detected_emotions", result)
        self.assertIn("timestamp", result)
        
    def test_process_handwriting(self):
        """Test handwriting recognition"""
        mock_image_data = "bW9jayBpbWFnZSBkYXRh"  # Base64 for "mock image data"
        
        result = process_handwriting(mock_image_data)
        
        self.assertIsInstance(result, dict)
        self.assertIn("transcription", result)
        self.assertIn("confidence", result)
        self.assertIn("detected_content_type", result)
        self.assertIn("equation_type", result)
        self.assertIn("parsed_latex", result)
        self.assertIn("timestamp", result)


class TestAssessmentUtils(unittest.TestCase):
    """Test cases for assessment utility functions"""
    
    def test_generate_question_algebra_basics(self):
        """Test question generation for algebra basics"""
        concept_id = "math_algebra_basics"
        difficulty = 2
        
        question = generate_question(concept_id, difficulty)
        
        self.assertIsInstance(question, dict)
        self.assertIn("id", question)
        self.assertEqual(question["concept_id"], concept_id)
        self.assertEqual(question["difficulty"], difficulty)
        self.assertIn("text", question)
        self.assertIn("solution", question)
        self.assertIn("answer", question)
        self.assertIn("variables", question)
    
    def test_generate_question_linear_equations(self):
        """Test question generation for linear equations"""
        concept_id = "math_algebra_linear_equations"
        difficulty = 3
        
        question = generate_question(concept_id, difficulty)
        
        self.assertIsInstance(question, dict)
        self.assertEqual(question["concept_id"], concept_id)
        self.assertEqual(question["difficulty"], difficulty)
        self.assertIn("text", question)
        self.assertIn("solution", question)
        self.assertIn("answer", question)
    
    def test_evaluate_student_answer_correct(self):
        """Test student answer evaluation - correct answer"""
        question = {
            "id": "q_test_123",
            "concept_id": "math_algebra_basics",
            "difficulty": 2,
            "text": "Solve: x + 5 = 8",
            "solution": "x + 5 = 8\nx = 8 - 5\nx = 3",
            "answer": "x = 3",
            "variables": {"a": 5, "b": 8}
        }
        
        # Test correct answer
        correct_answer = "x = 3"
        result = evaluate_student_answer(question, correct_answer)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["question_id"], question["id"])
        self.assertTrue(result["is_correct"])
        self.assertIsNone(result["error_type"])
        self.assertEqual(result["correct_answer"], question["answer"])
        self.assertEqual(result["student_answer"], correct_answer)
        
    def test_evaluate_student_answer_incorrect(self):
        """Test student answer evaluation - incorrect answer"""
        question = {
            "id": "q_test_456",
            "concept_id": "math_algebra_linear_equations",
            "difficulty": 3,
            "text": "Solve: 2x + 3 = 9",
            "solution": "2x + 3 = 9\n2x = 9 - 3\n2x = 6\nx = 6/2\nx = 3",
            "answer": "x = 3",
            "variables": {"a": 2, "b": 3, "c": 9}
        }
        
        # Test incorrect answer
        incorrect_answer = "x = 4"
        result = evaluate_student_answer(question, incorrect_answer)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["question_id"], question["id"])
        self.assertFalse(result["is_correct"])
        self.assertEqual(result["correct_answer"], question["answer"])
        self.assertEqual(result["student_answer"], incorrect_answer)


if __name__ == "__main__":
    unittest.main()
