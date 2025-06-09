"""
Gradio app for document OCR processing with Mistral OCR.

Features:
- File upload to storage API
- Document processing using Mistral OCR
- Display of OCR results
"""

import os
import requests
import gradio as gr
import asyncio
import json
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path

# Mistral AI
from mistralai import Mistral

# API Configuration
STORAGE_API_URL = "https://storage-bucket-api.vercel.app/upload"
MISTRAL_API_KEY = "5oHGQTYDGD3ecQZSqdLsr5ZL4nOsfGYj"  # In production, use environment variables

# Initialize Mistral client
client = Mistral(api_key=MISTRAL_API_KEY)

class MistralOCRProcessor:
    """Handles document OCR processing using Mistral AI"""
    
    def __init__(self, client: Mistral = None):
        self.client = client or Mistral(api_key=MISTRAL_API_KEY)
    
    async def process_document(self, document_path: str) -> Dict[str, Any]:
        """
        Process a document using Mistral OCR
        
        Args:
            document_path: Local path to the document to process
            
        Returns:
            Dict containing OCR results or error information
        """
        try:
            # For local files, we need to upload to a temporary URL first
            upload_result = await StorageManager().upload_file(document_path)
            if not upload_result.get("success"):
                return {
                    "success": False,
                    "result": None,
                    "error": f"Upload failed: {upload_result.get('error')}"
                }
            
            document_url = upload_result.get("storage_url")
            if not document_url:
                return {
                    "success": False,
                    "result": None,
                    "error": "No storage URL returned from upload"
                }
            
            # Process with Mistral OCR
            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": document_url
                },
                include_image_base64=True
            )
            
            # Convert response to dict if it's a Pydantic model
            if hasattr(ocr_response, 'model_dump'):
                result = ocr_response.model_dump()
            else:
                result = ocr_response
                
            return {
                "success": True,
                "result": result,
                "document_url": document_url,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": f"OCR processing error: {str(e)}"
            }

class StorageManager:
    """Handles file uploads to the storage service"""
    
    def __init__(self, api_url: str = STORAGE_API_URL):
        self.api_url = api_url
    
    async def upload_file(self, file_path: str) -> Dict[str, Any]:
        """
        Upload a file to the storage service
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            Dict containing upload result or error information
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                response = requests.post(self.api_url, files=files)
                response.raise_for_status()
                result = response.json()
                
                if not result.get('success'):
                    raise Exception(result.get('message', 'Upload failed'))
                    
                return {
                    "success": True,
                    "storage_url": result.get('storage_url'),
                    "original_filename": result.get('original_filename'),
                    "file_size": result.get('file_size'),
                    "error": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "storage_url": None,
                "original_filename": os.path.basename(file_path),
                "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                "error": f"Upload failed: {str(e)}"
            }

# Initialize processors
ocr_processor = MistralOCRProcessor()
storage_manager = StorageManager()

async def process_document_ocr(file_path: str) -> Dict[str, Any]:
    """
    Process a document through the complete OCR pipeline
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Dict containing processing results
    """
    # Process with Mistral OCR (handles upload internally)
    result = await ocr_processor.process_document(file_path)
    
    if not result.get("success"):
        return {
            "success": False,
            "upload": {"success": False},
            "ocr": None,
            "error": result.get("error", "Unknown error")
        }
    
    # Get the original filename from the file path
    original_filename = Path(file_path).name
    file_size = os.path.getsize(file_path)
    
    return {
        "success": True,
        "upload": {
            "success": True,
            "storage_url": result.get("document_url"),
            "original_filename": original_filename,
            "file_size": file_size
        },
        "ocr": result.get("result"),
        "error": None,
        "storage_url": result.get("document_url")
    }

# Gradio Interface
def create_gradio_interface():
    """Create and return the Gradio interface"""
    with gr.Blocks(title="Document OCR Processor", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# Document OCR Processor")
        gr.Markdown("Upload a document (PDF, JPG, JPEG, PNG) to process with Mistral OCR")
        
        with gr.Row():
            with gr.Column(scale=2):
                file_input = gr.File(label="Upload Document", type="filepath")
                process_btn = gr.Button("Process Document", variant="primary")
                
                with gr.Accordion("Debug Info", open=False):
                    status_text = gr.Textbox(label="Status", interactive=False)
                    
            with gr.Column(scale=3):
                with gr.Tabs():
                    with gr.TabItem("OCR Results"):
                        ocr_output = gr.JSON(label="OCR Output")
                    with gr.TabItem("Extracted Text"):
                        text_output = gr.Textbox(label="Extracted Text", lines=20, max_lines=50)
                    with gr.TabItem("Upload Info"):
                        upload_info = gr.JSON(label="Upload Information")
        
        def update_status(message):
            return message
        
        async def process_file(file_path):
            try:
                status = "Starting document processing..."
                yield {status_text: update_status(status)}
                
                # Process the document
                result = await process_document_ocr(file_path)
                
                if not result["success"]:
                    error_msg = result.get('error', 'Unknown error')
                    yield {
                        status_text: update_status(f"❌ {error_msg}"),
                        ocr_output: None,
                        text_output: "",
                        upload_info: None
                    }
                    return
                
                # Extract text from OCR result
                extracted_text = ""
                ocr_data = result.get("ocr", {})
                
                # Handle different OCR result formats
                if isinstance(ocr_data, dict):
                    if "text" in ocr_data:
                        extracted_text = ocr_data["text"]
                    elif "pages" in ocr_data and isinstance(ocr_data["pages"], list):
                        extracted_text = "\n\n".join(
                            page.get("text", "") 
                            for page in ocr_data["pages"] 
                            if page and isinstance(page, dict) and "text" in page
                        )
                
                # Prepare upload info
                upload_info_data = {
                    "original_filename": result["upload"].get("original_filename"),
                    "file_size": result["upload"].get("file_size"),
                    "storage_url": result["upload"].get("storage_url"),
                }
                
                yield {
                    status_text: update_status("✅ Document processed successfully"),
                    ocr_output: ocr_data,
                    text_output: extracted_text,
                    upload_info: upload_info_data
                }
                
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                error_msg = f"Unexpected error: {str(e)}"
                yield {
                    status_text: update_status(f"❌ {error_msg}"),
                    ocr_output: None,
                    text_output: "",
                    upload_info: None
                }
        
        # Connect the process button to the processing function
        process_btn.click(
            fn=process_file,
            inputs=file_input,
            outputs=[status_text, ocr_output, text_output, upload_info]
        )
        
        # Auto-process when a file is uploaded
        file_input.change(
            fn=lambda x: "Ready to process. Click 'Process Document' to continue.",
            inputs=file_input,
            outputs=status_text
        )
    
    return demo.launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    # Create and launch the interface
    create_gradio_interface()
