import pytest
import asyncio
import base64
import os
from mcp import ClientSession
from mcp.client.sse import sse_client

SERVER_URL = "http://localhost:8000/sse"  # Adjust if needed

@pytest.mark.asyncio
async def test_get_concept_graph_tool():
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            result = await session.call_tool("get_concept_graph_tool", {"concept_id": "python"})
            assert result and "error" not in result

@pytest.mark.asyncio
async def test_generate_quiz_tool():
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            result = await session.call_tool("generate_quiz_tool", {"concept": "python", "difficulty": "easy"})
            assert result and "error" not in result

@pytest.mark.asyncio
async def test_generate_lesson_tool():
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            result = await session.call_tool("generate_lesson_tool", {"topic": "Algebra", "grade_level": 8, "duration_minutes": 45})
            assert result and "error" not in result

@pytest.mark.asyncio
async def test_get_learning_path():
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            result = await session.call_tool("get_learning_path", {"student_id": "student_1", "concept_ids": ["python", "oop"], "student_level": "beginner"})
            assert result and "error" not in result

@pytest.mark.asyncio
async def test_text_interaction():
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            result = await session.call_tool("text_interaction", {"query": "What is a function in Python?", "student_id": "student_1"})
            assert result and "error" not in result

@pytest.mark.asyncio
async def test_check_submission_originality():
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            result = await session.call_tool("check_submission_originality", {"submission": "Python is a programming language.", "reference_sources": ["Python is a programming language.", "Java is another language."]})
            assert result and "error" not in result

@pytest.mark.asyncio
async def test_pdf_ocr(tmp_path):
    # Create a dummy PDF file
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4 test pdf content")
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    pdf_b64 = base64.b64encode(pdf_data).decode("utf-8")
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            result = await session.call_tool("pdf_ocr", {"pdf_data": pdf_b64, "filename": "test.pdf"})
            assert result and ("error" not in result or "Error processing PDF" in result.get("error", ""))

@pytest.mark.asyncio
async def test_image_to_text():
    # Create a dummy image (1x1 pixel PNG)
    import io
    from PIL import Image
    img = Image.new("RGB", (1, 1), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            result = await session.call_tool("image_to_text", {"image_data": img_b64})
            assert result and "error" not in result

@pytest.mark.asyncio
async def test_get_concept_tool():
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            result = await session.call_tool("get_concept_tool", {"concept_id": "python"})
            assert result and "error" not in result

@pytest.mark.asyncio
async def test_assess_skill_tool():
    async with sse_client(SERVER_URL) as (sse, write):
        async with ClientSession(sse, write) as session:
            await session.initialize()
            result = await session.call_tool("assess_skill_tool", {"student_id": "student_1", "concept_id": "python"})
            assert result and "error" not in result

if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__])) 