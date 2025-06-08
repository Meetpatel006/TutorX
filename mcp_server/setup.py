from setuptools import setup, find_packages

setup(
    name="mcp-server",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "mcp[cli]>=1.9.3",
        "pymupdf>=1.19.0",
        "pytesseract>=0.3.8",
        "Pillow>=8.3.1",
        "numpy>=1.21.0",
    ],
    python_requires=">=3.8",
)
