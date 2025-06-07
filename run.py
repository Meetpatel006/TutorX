"""
Script to run either the MCP server or the Gradio interface
"""

import argparse
import importlib.util
import os
import sys

def load_module(name, path):
    """Load a module from path"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_mcp_server():
    """Run the MCP server"""
    print("Starting TutorX MCP Server...")
    main_module = load_module("main", "main.py")
    
    # Access the mcp instance and run it
    if hasattr(main_module, "mcp"):
        main_module.mcp.run()
    else:
        print("Error: MCP server instance not found in main.py")
        sys.exit(1)

def run_gradio_interface():
    """Run the Gradio interface"""
    print("Starting TutorX Gradio Interface...")
    app_module = load_module("app", "app.py")
    
    # Run the Gradio demo
    if hasattr(app_module, "demo"):
        app_module.demo.launch()
    else:
        print("Error: Gradio demo not found in app.py")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TutorX MCP Server or Gradio Interface")
    parser.add_argument(
        "--mode", 
        choices=["mcp", "gradio", "both"], 
        default="mcp",
        help="Run mode: 'mcp' for MCP server, 'gradio' for Gradio interface, 'both' for both"
    )
    parser.add_argument(
        "--host", 
        default="127.0.0.1",
        help="Host address to use"
    )
    parser.add_argument(
        "--port", 
        type=int,
        default=8000,
        help="Port to use"
    )
    
    args = parser.parse_args()
    
    if args.mode == "mcp":
        # Set environment variables for MCP server
        os.environ["MCP_HOST"] = args.host
        os.environ["MCP_PORT"] = str(args.port)
        run_mcp_server()
    elif args.mode == "gradio":
        run_gradio_interface()
    elif args.mode == "both":
        # For 'both' mode, we'll start MCP server in a separate process
        import subprocess
        import time
        
        # Start MCP server in a background process
        mcp_process = subprocess.Popen(
            [sys.executable, "run.py", "--mode", "mcp", "--host", args.host, "--port", str(args.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give the MCP server a moment to start up
        print("Starting MCP server in background...")
        time.sleep(2)
        
        try:
            # Then start Gradio interface
            run_gradio_interface()
        finally:
            # Make sure to terminate the MCP server process when exiting
            print("Shutting down MCP server...")
            mcp_process.terminate()
            mcp_process.wait(timeout=5)
