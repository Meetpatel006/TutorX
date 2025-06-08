"""
Script to run either the MCP server or the Gradio interface for TutorX
"""

import os
import sys
import argparse
import uvicorn
from pathlib import Path
import socket

def run_mcp_server(host="0.0.0.0", port=8001):
    """
    Run the MCP server using uvicorn
    
    Args:
        host: Host to bind the server to
        port: Port to run the server on
    """
    print(f"Starting TutorX MCP Server on {host}:{port}...")
    
    # Set environment variables
    os.environ["MCP_HOST"] = host
    os.environ["MCP_PORT"] = str(port)
    
    try:
        # Add the mcp-server directory to Python path
        mcp_server_dir = str(Path(__file__).parent / "mcp-server")
        if mcp_server_dir not in sys.path:
            sys.path.insert(0, mcp_server_dir)
        
        # Import the FastAPI app
        from server import api_app
        
        # Run the server using uvicorn
        uvicorn.run(
            "mcp-server.server:api_app",
            host=host,
            port=port,
            reload=True,
            reload_dirs=[mcp_server_dir],
            log_level="info"
        )
    except ImportError as e:
        print(f"Error: {e}")
        print("Make sure you have installed all required dependencies:")
        print("  pip install uvicorn fastapi")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting MCP server: {e}")
        sys.exit(1)

def run_gradio_interface(port=7860):
    """
    Run the Gradio interface
    
    Args:
        port: Port to run the Gradio interface on
    """
    print(f"Starting TutorX Gradio Interface on port {port}...")
    
    try:
        # Make sure the mcp-server directory is in the path
        mcp_server_dir = str(Path(__file__).parent / "mcp-server")
        if mcp_server_dir not in sys.path:
            sys.path.insert(0, mcp_server_dir)
            
        # Import and run the Gradio app
        from app import demo
        
        # Launch the Gradio interface
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
        default=8001,
        help="Port for MCP server (default: 8001)"
    )
    parser.add_argument(
        "--gradio-port", 
        type=int, 
        default=7860,
        help="Port for Gradio interface (default: 7860)"
    )
    
    args = parser.parse_args()
    
    # Check if ports are available
    if args.mode in ["mcp", "both"] and not check_port_available(args.mcp_port):
        print(f"Error: Port {args.mcp_port} is already in use (MCP server)")
        sys.exit(1)
        
    if args.mode in ["gradio", "both"] and not check_port_available(args.gradio_port):
        print(f"Error: Port {args.gradio_port} is already in use (Gradio interface)")
        sys.exit(1)
    
    try:
        if args.mode in ["mcp", "both"]:
            # Start MCP server in a separate process
            mcp_process = multiprocessing.Process(
                target=run_mcp_server,
                kwargs={
                    "host": args.host,
                    "port": args.mcp_port
                }
            )
            mcp_process.start()
            
            # Give the server a moment to start
            time.sleep(2)
        
        if args.mode in ["gradio", "both"]:
            # Run Gradio in the main process
            run_gradio_interface(port=args.gradio_port)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if 'mcp_process' in locals() and mcp_process.is_alive():
            mcp_process.terminate()
            mcp_process.join(timeout=5)
