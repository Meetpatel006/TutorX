"""
OCR (Optical Character Recognition) tools for TutorX with Mistral OCR integration.
"""
import os
from typing import Dict, Any, Optional
from mcp_server.mcp_instance import mcp
from mcp_server.model.gemini_flash import GeminiFlash
from mistralai import Mistral

# Initialize models
MODEL = GeminiFlash()
client = Mistral(api_key="5oHGQTYDGD3ecQZSqdLsr5ZL4nOsfGYj")

async def mistral_ocr_request(document_url: str) -> dict:
    """
    Send OCR request to Mistral OCR service using document URL.
    
    Args:
        document_url: URL of the document to process
        
    Returns:
        OCR response from Mistral
    """
    try:
        # Process document with Mistral OCR
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": document_url
            },
            include_image_base64=True
        )
        
        # Convert the response to a dictionary
        if hasattr(ocr_response, 'model_dump'):
            return ocr_response.model_dump()
        return ocr_response or {}
        
    except Exception as e:
        raise RuntimeError(f"Error processing document with Mistral OCR: {str(e)}")

@mcp.tool()
async def mistral_document_ocr(document_url: str) -> dict:
    """
    Extract text from any document (PDF, image, etc.) using Mistral OCR service with document URL,
    then use Gemini to summarize and extract key points as JSON.
    
    Args:
        document_url (str): URL of the document to process
    
    Returns:
        Dictionary with OCR results and AI analysis
    """
    try:
        if not document_url:
            return {"error": "Document URL is required"}
        
        # Extract filename from URL
        filename = document_url.split('/')[-1] if '/' in document_url else "document"
        
        # Call Mistral OCR API
        ocr_response = await mistral_ocr_request(document_url)
        
        # Extract text from Mistral response
        extracted_text = ""
        page_count = 0
        
        if "pages" in ocr_response and isinstance(ocr_response["pages"], list):
            # Extract text from each page's markdown field
            extracted_text = "\n\n".join(
                page.get("markdown", "") 
                for page in ocr_response["pages"] 
                if isinstance(page, dict) and "markdown" in page
            )
            page_count = len(ocr_response["pages"])
        
        # Count words and characters
        word_count = len(extracted_text.split())
        char_count = len(extracted_text)
        
        # Build result
        result = {
            "success": True,
            "filename": filename,
            "document_url": document_url,
            "extracted_text": extracted_text,
            "character_count": char_count,
            "word_count": word_count,
            "page_count": page_count,
            "mistral_response": ocr_response,
            "processing_service": "Mistral OCR",
            "llm_analysis": {
                "error": None,
                "summary": "",
                "key_points": [],
                "document_type": "unknown"
            }
        }
        
        # If we have text, try to analyze it with the LLM
        if extracted_text.strip():
            try:
                # Use the LLM to analyze the extracted text
                llm_prompt = f"""Analyze the following document and provide a brief summary, 3-5 key points, and the document type.

Document:
{extracted_text[:4000]}  # Limit to first 4000 chars to avoid context window issues
"""
                
                # Await the coroutine
                llm_response = await MODEL.generate_text(llm_prompt)
                
                # Parse the LLM response
                if llm_response:
                    # Try to parse as JSON if the response is in JSON format
                    try:
                        import json
                        llm_data = json.loads(llm_response)
                        result["llm_analysis"].update({
                            "summary": llm_data.get("summary", ""),
                            "key_points": llm_data.get("key_points", []),
                            "document_type": llm_data.get("document_type", "document")
                        })
                    except (json.JSONDecodeError, AttributeError):
                        # If not JSON, use the raw response as summary
                        result["llm_analysis"].update({
                            "summary": str(llm_response),
                            "document_type": "document"
                        })
                    
            except Exception as e:
                result["llm_analysis"]["error"] = f"LLM analysis error: {str(e)}"
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error processing document with Mistral OCR: {str(e)}",
            "document_url": document_url
        }