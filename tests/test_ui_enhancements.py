#!/usr/bin/env python3
"""
Test script for TutorX UI/UX enhancements
This script validates the UI improvements and provides a quick way to test the interface.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'gradio',
        'matplotlib',
        'networkx',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def validate_ui_components():
    """Validate that UI enhancement components are properly implemented"""
    print("\n🔍 Validating UI components...")
    
    try:
        # Import the app module to check for syntax errors
        sys.path.insert(0, os.getcwd())
        import app
        
        # Check if helper functions exist
        helper_functions = [
            'create_info_card',
            'create_status_display', 
            'create_feature_section'
        ]
        
        for func_name in helper_functions:
            if hasattr(app, func_name):
                print(f"✅ {func_name} function is available")
            else:
                print(f"❌ {func_name} function is missing")
                return False
        
        # Check if the main interface function exists
        if hasattr(app, 'create_gradio_interface'):
            print("✅ create_gradio_interface function is available")
        else:
            print("❌ create_gradio_interface function is missing")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error importing app module: {str(e)}")
        return False

def test_interface_creation():
    """Test if the Gradio interface can be created without errors"""
    print("\n🧪 Testing interface creation...")
    
    try:
        sys.path.insert(0, os.getcwd())
        import app
        
        # Try to create the interface
        demo = app.create_gradio_interface()
        print("✅ Gradio interface created successfully")
        
        # Check if demo has the expected properties
        if hasattr(demo, 'queue'):
            print("✅ Interface has queue method")
        else:
            print("❌ Interface missing queue method")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating interface: {str(e)}")
        return False

def run_ui_test():
    """Run a quick UI test by launching the interface briefly"""
    print("\n🚀 Running UI test...")
    
    try:
        # Launch the app in a subprocess for a brief test
        process = subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a few seconds to see if it starts successfully
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ UI launched successfully")
            process.terminate()
            process.wait()
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ UI failed to launch")
            if stderr:
                print(f"Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running UI test: {str(e)}")
        return False

def check_documentation():
    """Check if UI/UX documentation exists"""
    print("\n📚 Checking documentation...")
    
    doc_file = Path("docs/UI_UX_ENHANCEMENTS.md")
    if doc_file.exists():
        print("✅ UI/UX enhancement documentation exists")
        
        # Check file size to ensure it has content
        if doc_file.stat().st_size > 1000:
            print("✅ Documentation has substantial content")
        else:
            print("⚠️  Documentation file is quite small")
            
        return True
    else:
        print("❌ UI/UX enhancement documentation is missing")
        return False

def main():
    """Main test function"""
    print("🧠 TutorX UI/UX Enhancement Test Suite")
    print("=" * 50)
    
    tests = [
        ("Dependencies Check", check_dependencies),
        ("UI Components Validation", validate_ui_components),
        ("Interface Creation Test", test_interface_creation),
        ("Documentation Check", check_documentation),
        ("UI Launch Test", run_ui_test)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔄 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! UI enhancements are working correctly.")
        print("\n🚀 You can now run the app with: python app.py")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
