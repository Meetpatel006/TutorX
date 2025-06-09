---
title: TutorX MCP
emoji: 🏆
colorFrom: indigo
colorTo: yellow
sdk: gradio
sdk_version: 5.33.0
app_file: app.py
pinned: false
short_description: MCP that deliver personalized AI-powered tutoring .
---

# TutorX-MCP Server

A comprehensive Model Context Protocol (MCP) server for educational AI tutoring as specified in the Product Requirements Document (PRD).

## Overview

TutorX-MCP is an adaptive, multi-modal, and collaborative AI tutoring platform that leverages the Model Context Protocol (MCP) for tool integration and Gradio for user-friendly interfaces. It provides a range of educational features accessible via both MCP clients and a dedicated web interface.

![TutorX-MCP](https://via.placeholder.com/800x400?text=TutorX-MCP+Educational+Platform)

For a comprehensive analysis of the project from architectural, development, and product perspectives, please see our [Project Analysis Document](PROJECT_ANALYSIS.md).

## Version History

### Current Version
- **v0.1.0** (June 2025)
  - Initial release of core MCP server with SSE transport
  - Implementation of concept graph and curriculum standards resources
  - Integration with Google Gemini Flash models (with fallback mechanism)
  - Addition of Mistral OCR for document processing
  - Core educational tools: concepts, quizzes, lessons, learning paths
  - Basic testing framework with pytest and unittest

### Upcoming Release
- **v0.2.0** (Planned - July 2025)
  - Memory Bank implementation for persistent context storage
  - Enhanced multi-modal support with voice recognition
  - Improved testing coverage and CI/CD pipeline
  - User dashboard implementation
  - Role-based access control and security enhancements

## Features

### Core Features

- **Adaptive Learning Engine**
  - Comprehensive concept graph
  - Dynamic skill assessment and tracking
  - Personalized learning paths

- **Assessment Suite**
  - Automated quiz and problem generation
  - Step-by-step solution analysis
  - Plagiarism and similarity detection

- **Feedback System**
  - Contextual error analysis and suggestions
  - Error pattern recognition

- **Multi-Modal Interaction**
  - Text-based Q&A with error pattern recognition
  - Voice recognition with analysis
  - Handwriting recognition and digital ink processing

### Advanced Features

- **Neurological Engagement Monitor**
  - Attention, cognitive load, and stress detection

- **Cross-Institutional Knowledge Fusion**
  - Curriculum alignment with national standards
  - Content reconciliation

- **Automated Lesson Authoring**
  - AI-powered content generation

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Dependencies as listed in pyproject.toml:
  - mcp[cli] >= 1.9.3
  - fastapi >= 0.109.0
  - uvicorn >= 0.27.0
  - gradio >= 4.19.0
  - numpy >= 1.24.0
  - pillow >= 10.0.0
  - google-generativeai (for Gemini integration)
  - mistralai (for OCR capabilities)

### Installation

```powershell
# Clone the repository
git clone https://github.com/Meetpatel006/TutorX.git
cd tutorx-mcp

# Using uv (recommended)
uv install

```

### Required API Keys

For full functionality, you'll need to set up the following API keys:

- **Google AI API Key**: For Gemini Flash model integration
- **Mistral API Key**: For document OCR capabilities

These can be set as environment variables or in an `.env` file:

```powershell
# PowerShell example
$env:GOOGLE_API_KEY="your-google-api-key"
$env:MISTRAL_API_KEY="your-mistral-api-key"
```

### Running the Server

You can run the server in different modes:

```powershell
# MCP server only
python run.py --mode mcp

# Gradio interface only
python run.py --mode gradio

# Both MCP server and Gradio interface (default)
python run.py --mode both

# Custom host and port
python run.py --mode mcp --host 0.0.0.0 --mcp-port 8000 --gradio-port 7860
```

By default:
- The MCP server runs at http://localhost:8000 
- SSE transport is available at http://localhost:8000/sse
- The Gradio interface runs at http://127.0.0.1:7860

## MCP Tool Integration

The server exposes the following MCP tools and resources:

### Tools

- **Concept Tools** (concept_tools.py)
  - `get_concept_tool`: Retrieve detailed information about educational concepts
  - `assess_skill_tool`: Evaluate student's understanding of specific concepts

- **Quiz Tools** (quiz_tools.py)
  - `generate_quiz_tool`: Create LLM-generated quizzes for specific concepts with customizable difficulty

- **Lesson Tools** (lesson_tools.py)
  - `generate_lesson_tool`: Create complete lesson plans with objectives, activities, and assessments

- **Interaction Tools** (interaction_tools.py)
  - `text_interaction`: Process student text queries and provide educational responses
  - `check_submission_originality`: Analyze student submissions for potential plagiarism

- **OCR Tools** (ocr_tools.py)
  - `mistral_document_ocr`: Extract and process text from documents using Mistral OCR

- **Learning Path Tools** (learning_path_tools.py)
  - `get_learning_path`: Generate personalized learning paths based on student level and target concepts

- **Memory Tools** (v0.2.0)
  - `read_memory_tool`: Retrieve stored context from the Memory Bank
  - `write_memory_tool`: Store new contextual information in the Memory Bank
  - `update_memory_tool`: Modify existing context in the Memory Bank
  - `clear_memory_tool`: Remove stored context from the Memory Bank

### Resources

- `concept-graph://`: Knowledge concept graph with concept relationships
- `curriculum-standards://{country_code}`: National curricular standards by country
- `learning-path://{student_id}`: Personalized student learning paths


## Project Structure

```
tutorx-mcp/
├── main.py                  # MCP server entry point
├── app.py                   # Gradio web interface
├── run.py                   # Runner script for different modes
├── mcp_server/              # Core server implementation
│   ├── server.py            # FastAPI application
│   ├── mcp_instance.py      # Shared MCP instance
│   ├── model/               # AI model integrations
│   │   └── gemini_flash.py  # Google Gemini integration
│   ├── resources/           # Educational resources
│   │   ├── concept_graph.py # Concept graph implementation
│   │   └── curriculum_standards.py # Curriculum standards
│   ├── tools/               # MCP tool implementations
│   │   ├── concept_tools.py # Concept-related tools
│   │   ├── quiz_tools.py    # Quiz generation tools
│   │   ├── lesson_tools.py  # Lesson generation tools
│   │   ├── ocr_tools.py     # Document OCR tools
│   │   ├── interaction_tools.py # Student interaction tools
│   │   └── learning_path_tools.py # Learning path tools
│   └── prompts/             # LLM prompt templates
├── tests/                   # Test suite
│   ├── test_mcp_server.py   # MCP server tests
│   ├── test_client.py       # Client tests
│   ├── test_tools_integration.py # Tool integration tests
│   └── test_utils.py        # Utility function tests
├── docs/                    # Documentation
│   ├── API.md               # API documentation
│   ├── mcp.md               # MCP protocol details
│   ├── prd.md               # Product requirements document
│   └── sdk.md               # Client SDK documentation
├── pyproject.toml           # Project dependencies
├── run_tests.py             # Script to run all tests
├── ARCHITECTURE.md          # Detailed architecture documentation
├── PROJECT_ANALYSIS.md      # Comprehensive project analysis
└── README.md                # Project documentation
```

## Architecture

TutorX-MCP implements a modular, layered architecture designed for extensibility and maintainability:

### Key Components

1. **MCP Server (mcp_server/server.py)**: 
   - Core FastAPI application that exposes educational tools and resources
   - Registers tools with the shared MCP instance
   - Provides HTTP endpoints and SSE transport for client connections

2. **Shared MCP Instance (mcp_server/mcp_instance.py)**: 
   - Central registration point for all MCP tools
   - Avoids circular import issues and ensures tool availability

3. **AI Model Integration (mcp_server/model/)**:
   - Integrates Google Gemini Flash models with automatic fallback mechanisms
   - Provides uniform interface for text generation and content structuring

4. **Tool Modules (mcp_server/tools/)**:
   - Modular implementation of educational features
   - Each tool is registered with the MCP instance via decorators
   - Designed for independent development and testing

5. **Resource Modules (mcp_server/resources/)**:
   - Manages educational data like concept graphs and curriculum standards
   - Provides data for adaptive learning and standards alignment

6. **Gradio Interface (app.py)**:
   - Web-based user interface
   - Communicates with the MCP server via the MCP client protocol

This separation of concerns allows:
- MCP clients (like Claude Desktop App) to directly connect to the MCP server via SSE transport
- The web interface to interact with the server using the MCP protocol
- Clear boundaries between presentation, API gateway, tool implementations, and resources
- Easy extension through the addition of new tool modules

For more detailed architecture information, see the [Architecture Documentation](ARCHITECTURE.md) and [Project Analysis](PROJECT_ANALYSIS.md).

## Testing

The project includes a comprehensive test suite:

```bash
# Install test dependencies
uv install -e ".[test]"

# Run test suite
python run_tests.py
```

## Documentation

- [Project Analysis](PROJECT_ANALYSIS.md): Comprehensive analysis of architecture, implementation, and product features
- [MCP Protocol](docs/mcp.md): Details about the Model Context Protocol
- [Product Requirements](docs/prd.md): Original requirements document
- [SDK Documentation](docs/sdk.md): Client SDK usage
- [Architecture](ARCHITECTURE.md): Detailed technical architecture documentation

## Contributing

We welcome contributions to the TutorX-MCP project! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
