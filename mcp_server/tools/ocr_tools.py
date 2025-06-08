"""
OCR (Optical Character Recognition) tools for TutorX.
"""
import base64
import io
import tempfile
from typing import Dict, Any, Optional, Tuple
# import fitz  # PyMuPDFuv run 
import pytesseract
from PIL import Image, ImageEnhance
import numpy as np
from mcp_server.mcp_instance import mcp

def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Preprocess image to improve OCR accuracy.
    
    Args:
        image: Input PIL Image
        
    Returns:
        Preprocessed PIL Image
    """
    # Convert to grayscale
    image = image.convert('L')
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)
    
    return image

def extract_text_from_image(image: Image.Image) -> str:
    """
    Extract text from an image using Tesseract OCR.
    
    Args:
        image: PIL Image to process
        
    Returns:
        Extracted text
    """
    try:
        # Preprocess the image
        processed_image = preprocess_image(image)
        
        # Use Tesseract to do OCR on the image
        text = pytesseract.image_to_string(processed_image, lang='eng')
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"Error during OCR processing: {str(e)}")

def extract_text_from_pdf(pdf_data: bytes) -> Tuple[str, int]:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_data: PDF file content as bytes
        
    Returns:
        Tuple of (extracted_text, page_count)
    """
    try:
        # Open the PDF file
        with fitz.open(stream=pdf_data, filetype="pdf") as doc:
            page_count = len(doc)
            extracted_text = []
            
            # Extract text from each page
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                # If no text is found, try OCR
                if not text.strip():
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    text = extract_text_from_image(img)
                
                extracted_text.append(text)
            
            return "\n\n".join(extracted_text), page_count
    except Exception as e:
        raise RuntimeError(f"Error processing PDF: {str(e)}")

@mcp.tool()
async def pdf_ocr(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract text from a PDF file using OCR.
    
    Expected request format:
    {
        "pdf_data": "base64_encoded_pdf_data",
        "filename": "document.pdf"  # Optional
    }
    
    Returns:
        Dictionary containing extracted text and metadata
    """
    try:
        # Get and validate input
        pdf_data_b64 = request.get("pdf_data")
        if not pdf_data_b64:
            return {"error": "Missing required field: pdf_data"}
        
        # Decode base64 data
        try:
            pdf_data = base64.b64decode(pdf_data_b64)
        except Exception as e:
            return {"error": f"Invalid base64 data: {str(e)}"}
        
        # Extract text from PDF
        extracted_text, page_count = extract_text_from_pdf(pdf_data)
        
        # Prepare response
        result = {
            "success": True,
            "filename": request.get("filename", "document.pdf"),
            "page_count": page_count,
            "extracted_text": extracted_text,
            "character_count": len(extracted_text),
            "word_count": len(extracted_text.split()),
            "processing_time_ms": 0  # Could be calculated if needed
        }
        
        return result
        
    except Exception as e:
        return {"error": f"Error processing PDF: {str(e)}"}

@mcp.tool()
async def image_to_text(image_data: str) -> Dict[str, Any]:
    """
    Extract text from an image using OCR.
    
    Args:
        image_data: Base64 encoded image data
        
    Returns:
        Dictionary containing extracted text and metadata
    """
    try:
        # Decode base64 image data
        image_bytes = base64.b64decode(image_data)
        
        # Open image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Extract text
        text = extract_text_from_image(image)
        
        return {
            "success": True,
            "extracted_text": text,
            "character_count": len(text),
            "word_count": len(text.split()),
            "image_size": image.size,
            "image_mode": image.mode
        }
    except Exception as e:
        return {"error": f"Error processing image: {str(e)}"}
