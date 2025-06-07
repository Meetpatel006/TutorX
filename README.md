# TutorX-MCP Server

A comprehensive Model Context Protocol (MCP) server for educational AI tutoring as specified in the Product Requirements Document (PRD).

## Overview

TutorX-MCP is an adaptive, multi-modal, and collaborative AI tutoring platform that leverages the Model Context Protocol (MCP) for tool integration and Gradio for user-friendly interfaces. It provides a range of educational features accessible via both MCP clients and a dedicated web interface.

![TutorX-MCP](https://via.placeholder.com/800x400?text=TutorX-MCP+Educational+Platform)

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
  - gradio >= 4.19.0
  - numpy >= 1.24.0
  - pillow >= 10.0.0

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/tutorx-mcp.git
cd tutorx-mcp

# Using uv (recommended)
uv install

# Or using pip
pip install -e .
```

### Running the Server

You can run the server in different modes:

```bash
# MCP server only
python run.py --mode mcp

# Gradio interface only
python run.py --mode gradio

# Both MCP server and Gradio interface
python run.py --mode both

# Custom host and port
python run.py --mode mcp --host 0.0.0.0 --port 9000
```

By default, the MCP server will run at http://localhost:8000 and the Gradio interface at http://127.0.0.1:7860.

## MCP Tool Integration

The server exposes the following MCP tools and resources:

### Tools
- **Core Features**
  - `assess_skill`: Evaluate student's skill level on specific concepts
  - `generate_quiz`: Create quizzes for specific concepts
  - `analyze_error_patterns`: Find common student mistakes

- **Assessment**
  - `create_assessment`: Generate complete assessments
  - `grade_assessment`: Score student responses
  - `check_submission_originality`: Detect plagiarism

- **Advanced Features**
  - `analyze_cognitive_state`: Process EEG data
  - `align_content_to_standard`: Match content to curriculum standards
  - `generate_lesson`: Create complete lesson plans

- **Multi-Modal**
  - `text_interaction`: Process text queries
  - `voice_interaction`: Handle voice input
  - `handwriting_recognition`: Process handwritten input

### Resources
- `concept-graph://`: Knowledge concept graph
- `learning-path://{student_id}`: Personalized learning paths
- `curriculum-standards://{country_code}`: National curricular standards
- `student-dashboard://{student_id}`: Student performance dashboard

## Project Structure

```
tutorx-mcp/
├── main.py              # MCP server implementation
├── client.py            # MCP client for calling server tools
├── app.py               # Gradio web interface
├── run.py               # Runner script for different modes
├── utils/               # Utility modules
│   ├── multimodal.py    # Multi-modal processing utilities
│   └── assessment.py    # Assessment and analytics functions
├── pyproject.toml       # Project dependencies
└── README.md            # Project documentation
```

## Architecture

The TutorX-MCP follows a layered architecture:

1. **MCP Server (main.py)**: Core backend that exposes educational tools and resources through the Model Context Protocol.

2. **MCP Client (client.py)**: Client library that communicates with the MCP server through HTTP requests, translating method calls into MCP protocol interactions.

3. **Gradio Interface (app.py)**: Web-based user interface that uses the client to communicate with the MCP server.

This separation of concerns allows:
- MCP clients (like Claude Desktop App) to directly connect to the MCP server
- The web interface to interact with the server using standard HTTP
- Clear boundaries between presentation, business logic, and tool implementation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Model Context Protocol (MCP) - https://modelcontextprotocol.io/
- Gradio - https://gradio.app/