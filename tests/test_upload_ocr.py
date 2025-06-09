"""
Test script for file upload and OCR functionality.

This script tests the file upload to the storage API and verifies the OCR functionality with the returned storage URL.
"""

import os
import requests
import asyncio
import argparse
from pathlib import Path

# Configuration
STORAGE_API_URL = "https://storage-bucket-api.vercel.app/upload"

async def upload_file_to_storage(file_path):
    """Helper function to upload file to storage API"""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            print(f"Uploading {file_path} to storage...")
            response = requests.post(STORAGE_API_URL, files=files)
            response.raise_for_status()
            result = response.json()
            print("\nUpload successful! Response:")
            print(f"- Success: {result.get('success')}")
            print(f"- Message: {result.get('message')}")
            print(f"- Original filename: {result.get('original_filename')}")
            print(f"- Uploaded filename: {result.get('uploaded_filename')}")
            print(f"- File size: {result.get('file_size')} bytes")
            print(f"- Content type: {result.get('content_type')}")
            print(f"- Storage URL: {result.get('storage_url')}")
            return result
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Server response: {e.response.text}")
        return {"error": str(e), "success": False}

async def test_ocr_with_storage_url(storage_url):
    """Test OCR functionality with a storage URL"""
    print(f"\nTesting OCR with URL: {storage_url}")
    # This is a placeholder for the actual OCR test
    # You would typically call your OCR service here
    print("OCR test would process the document at:", storage_url)
    print("OCR test completed (mock implementation)")
    return {"success": True, "message": "OCR test completed (mock implementation)"}

async def main():
    parser = argparse.ArgumentParser(description='Test file upload and OCR functionality')
    parser.add_argument('file_path', type=str, help='Path to the file to upload and test')
    parser.add_argument('--test-ocr', action='store_true',
                      help='Test OCR functionality with the uploaded file')
    
    args = parser.parse_args()
    
    # Verify file exists
    if not os.path.exists(args.file_path):
        print(f"Error: File not found: {args.file_path}")
        return
    
    # Upload the file
    upload_result = await upload_file_to_storage(args.file_path)
    
    if not upload_result.get('success'):
        print("\nUpload failed. Cannot proceed with OCR test.")
        return
    
    storage_url = upload_result.get('storage_url')
    if not storage_url:
        print("\nNo storage URL in upload response. Cannot test OCR functionality.")
        return
    
    # Test OCR if requested
    if args.test_ocr:
        await test_ocr_with_storage_url(storage_url)

if __name__ == "__main__":
    asyncio.run(main())
