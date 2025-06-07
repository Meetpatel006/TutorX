"""
Script to run all tests for the TutorX MCP server
"""
import sys
import os
import unittest
import pytest

def run_tests():
    """Run all tests"""
    print("Running TutorX-MCP Tests...")
    
    # First run unittest tests
    unittest_loader = unittest.TestLoader()
    test_directory = os.path.join(os.path.dirname(__file__), "tests")
    test_suite = unittest_loader.discover(test_directory)
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    unittest_result = test_runner.run(test_suite)
    
    # Then run pytest tests (with coverage)
    pytest_args = [
        "tests", 
        "--cov=.",
        "--cov-report=term",
        "--cov-report=html:coverage_html",
        "-v"
    ]
    
    pytest_result = pytest.main(pytest_args)
    
    # Return success if both test runners succeeded
    return unittest_result.wasSuccessful() and pytest_result == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
