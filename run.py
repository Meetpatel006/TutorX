"""
Script to run either the MCP server or the Gradio interface
"""

import argparse
import importlib.util
import os
import sys
import time
import subprocess

def load_module(name, path):
    """Load a module from path"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_mcp_server(host="0.0.0.0", port=8001, transport="http"):
    """Run the MCP server with specified configuration"""
    print(f"Starting TutorX MCP Server on {host}:{port} using {transport} transport...")
    
    # Set environment variables for MCP server
    os.environ["MCP_HOST"] = host
    os.environ["MCP_PORT"] = str(port)
    os.environ["MCP_TRANSPORT"] = transport
    
    # Import and run the main module
    main_module = load_module("main", "main.py")
    
    # Access the mcp instance and run it
    if hasattr(main_module, "run_server"):
        main_module.run_server()
    else:
        print("Error: run_server function not found in main.py")
        sys.exit(1)

def run_gradio_interface():
    """Run the Gradio interface"""
    print("Starting TutorX Gradio Interface...")
    app_module = load_module("app", "app.py")
    
    # Run the Gradio demo
    if hasattr(app_module, "demo"):
        app_module.demo.launch(server_name="0.0.0.0", server_port=7860)
    else:
        print("Error: Gradio demo not found in app.py")
        sys.exit(1)

def check_port_available(port):
    """Check if a port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except:
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TutorX MCP Server or Gradio Interface")
    parser.add_argument(
        "--mode", 
        choices=["mcp", "gradio", "both"], 
        default="both",
        help="Run mode: 'mcp' for MCP server, 'gradio' for Gradio interface, 'both' for both"
    )
    parser.add_argument(
        "--host", 
        default="0.0.0.0",
        help="Host address to use"
    )
    parser.add_argument(
        "--port", 
        type=int,
        default=8001,
        help="Port to use for MCP server (default: 8001)"
    )
    parser.add_argument(
        "--gradio-port", 
        type=int,
        default=7860,
        help="Port to use for Gradio interface (default: 7860)"
    )
    parser.add_argument(
        "--transport",
        default="http",
        help="Transport protocol to use (default: http)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "mcp":
        if not check_port_available(args.port):
            print(f"Warning: Port {args.port} is already in use. Trying to use the server anyway...")
        run_mcp_server(args.host, args.port, args.transport)
    elif args.mode == "gradio":
        run_gradio_interface()
    elif args.mode == "both":
        # For 'both' mode, we'll start MCP server in a separate process
        if not check_port_available(args.port):
            print(f"Warning: Port {args.port} is already in use. Trying to use the server anyway...")
            
        # Start MCP server in a background process
        mcp_process = subprocess.Popen(
            [
                sys.executable, 
                "run.py", 
                "--mode", "mcp", 
                "--host", args.host, 
                "--port", str(args.port),
                "--transport", args.transport
            ],
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
