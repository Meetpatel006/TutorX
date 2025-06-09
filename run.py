"""
Script to run either the MCP server or the Gradio interface for TutorX
"""

import os
import sys
import time
import argparse
import subprocess
import multiprocessing
from pathlib import Path
import socket

def run_mcp_server(host="0.0.0.0", port=8000, debug=False):
    """
    Run the MCP server using uv
    
    Args:
        host: Host to bind the server to
        port: Port to run the server on
        debug: Whether to run in debug mode
    """
    print(f"Starting TutorX MCP Server on {host}:{port}...")
    
    # Set environment variables
    os.environ["MCP_HOST"] = host
    os.environ["MCP_PORT"] = str(port)
    if debug:
        os.environ["DEBUG"] = "1"
    
    try:
        # Build the command to run the server using uv
        cmd = [
            "uv", "run", "-m", "mcp_server.server",
            "--host", host,
            "--port", str(port)
        ]
        
        # Add debug flag if needed
        if debug:
            cmd.append("--debug")
        
        # Execute the command
        server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Print the first few lines of output to confirm server started
        for _ in range(5):
            line = server_process.stdout.readline()
            if not line:
                break
            print(line.strip())
        
        # Return the process so it can be managed by the caller
        return server_process
        
    except Exception as e:
        print(f"Error starting MCP server: {e}")
        print("Make sure you have installed all required dependencies:")
        print("  pip install uv")
        sys.exit(1)

def run_gradio_interface(port=7860):
    """
    Run the Gradio interface
    
    Args:
        port: Port to run the Gradio interface on
    """
    print(f"Starting TutorX Gradio Interface on port {port}...")
    
    try:
        # Make sure the mcp_server directory is in the path
        mcp_server_dir = str(Path(__file__).parent / "mcp_server")
        if mcp_server_dir not in sys.path:
            sys.path.insert(0, mcp_server_dir)
            
        # Import and create the Gradio app
        from app import create_gradio_interface
        
        # Create and launch the Gradio interface
        demo = create_gradio_interface()
        demo.launch(
            server_name="0.0.0.0",
            server_port=port,
            share=False
        )
    except Exception as e:
        print(f"Failed to start Gradio interface: {e}")
        sys.exit(1)

def check_port_available(port):
    """
    Check if a port is available
    
    Args:
        port: Port number to check
        
    Returns:
        bool: True if port is available, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TutorX - Run MCP Server and/or Gradio Interface"
    )
    
    # Add command line arguments
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["mcp", "gradio", "both"], 
        default="both",
        help="Run mode: 'mcp' for MCP server, 'gradio' for Gradio interface, 'both' for both (default)"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--mcp-port", 
        type=int, 
        default=8000,
        help="Port for MCP server (default: 8000)"
    )
    parser.add_argument(
        "--gradio-port", 
        type=int, 
        default=7860,
        help="Port for Gradio interface (default: 7860)"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Run with debug mode for more verbose output"
    )
    
    args = parser.parse_args()
    
    # Check if ports are available
    if args.mode in ["mcp", "both"] and not check_port_available(args.mcp_port):
        print(f"Error: Port {args.mcp_port} is already in use (MCP server)")
        sys.exit(1)
        
    if args.mode in ["gradio", "both"] and not check_port_available(args.gradio_port):
        print(f"Error: Port {args.gradio_port} is already in use (Gradio interface)")
        sys.exit(1)
    
    server_process = None
    
    try:
        if args.mode in ["mcp", "both"]:
            # Start MCP server using uv run
            print("Starting MCP server...")
            server_process = run_mcp_server(
                host=args.host,
                port=args.mcp_port,
                debug=args.debug
            )
            
            # Give the server a moment to start
            time.sleep(2)
            print(f"MCP server running at http://{args.host}:{args.mcp_port}")
            print(f"MCP SSE endpoint available at http://{args.host}:{args.mcp_port}/sse")
        
        if args.mode in ["gradio", "both"]:
            # Run Gradio in the main process
            print(f"Starting Gradio interface on port {args.gradio_port}...")
            run_gradio_interface(port=args.gradio_port)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        # Clean up the server process if it's running
        if server_process is not None:
            print("Terminating MCP server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
                print("Server process killed after timeout")
