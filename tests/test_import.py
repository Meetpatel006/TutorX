#!/usr/bin/env python3
"""
Simple test script to verify adaptive learning imports work correctly.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all adaptive learning imports."""
    print("🧪 Testing Adaptive Learning System Imports")
    print("=" * 50)
    
    try:
        print("1. Testing analytics imports...")
        from mcp_server.analytics.performance_tracker import PerformanceTracker
        from mcp_server.analytics.learning_analytics import LearningAnalytics
        from mcp_server.analytics.progress_monitor import ProgressMonitor
        print("   ✅ Analytics imports successful")
        
        print("2. Testing algorithms imports...")
        from mcp_server.algorithms.adaptive_engine import AdaptiveLearningEngine
        from mcp_server.algorithms.difficulty_adjuster import DifficultyAdjuster
        from mcp_server.algorithms.path_optimizer import PathOptimizer
        from mcp_server.algorithms.mastery_detector import MasteryDetector
        print("   ✅ Algorithms imports successful")
        
        print("3. Testing models imports...")
        from mcp_server.models.student_profile import StudentProfile
        print("   ✅ Models imports successful")
        
        print("4. Testing storage imports...")
        from mcp_server.storage.memory_store import MemoryStore
        print("   ✅ Storage imports successful")
        
        print("5. Testing component initialization...")
        performance_tracker = PerformanceTracker()
        learning_analytics = LearningAnalytics(performance_tracker)
        progress_monitor = ProgressMonitor(performance_tracker, learning_analytics)
        adaptive_engine = AdaptiveLearningEngine(performance_tracker, learning_analytics)
        difficulty_adjuster = DifficultyAdjuster(performance_tracker)
        path_optimizer = PathOptimizer(performance_tracker, learning_analytics)
        mastery_detector = MasteryDetector(performance_tracker)
        print("   ✅ Component initialization successful")
        
        print("6. Testing adaptive learning tools import...")
        import mcp_server.tools.adaptive_learning_tools
        print("   ✅ Adaptive learning tools import successful")
        
        print("\n🎉 All imports successful!")
        print("The adaptive learning system is ready to use.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality without async."""
    print("\n🔧 Testing Basic Functionality")
    print("=" * 50)
    
    try:
        from mcp_server.analytics.performance_tracker import PerformanceTracker
        from mcp_server.models.student_profile import StudentProfile
        from mcp_server.storage.memory_store import MemoryStore
        
        # Test performance tracker
        print("1. Testing PerformanceTracker...")
        tracker = PerformanceTracker()
        print(f"   ✅ Created tracker with {len(tracker.student_performances)} students")
        
        # Test student profile
        print("2. Testing StudentProfile...")
        profile = StudentProfile(student_id="test_001", name="Test Student")
        print(f"   ✅ Created profile for {profile.name}")
        
        # Test memory store
        print("3. Testing MemoryStore...")
        store = MemoryStore()
        store.save_student_profile(profile)
        retrieved = store.get_student_profile("test_001")
        print(f"   ✅ Stored and retrieved profile: {retrieved.name if retrieved else 'None'}")
        
        print("\n🎉 Basic functionality test successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧠 TutorX-MCP Adaptive Learning System - Import Test")
    print("=" * 60)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test basic functionality
        functionality_ok = test_basic_functionality()
        
        if functionality_ok:
            print("\n✅ All tests passed! The system is ready.")
            sys.exit(0)
        else:
            print("\n❌ Functionality tests failed.")
            sys.exit(1)
    else:
        print("\n❌ Import tests failed.")
        sys.exit(1)
