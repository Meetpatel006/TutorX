# Contributing to TutorX-MCP

Thank you for considering contributing to TutorX-MCP! This document outlines the process and guidelines for contributing to this project.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:

1. A clear, descriptive title
2. Steps to reproduce the issue
3. Expected behavior
4. Actual behavior
5. Any relevant logs or screenshots
6. Your environment (OS, Python version, etc.)

### Suggesting Enhancements

We welcome suggestions for enhancements! Please create an issue with:

1. A clear, descriptive title
2. Detailed description of the proposed enhancement
3. Any specific use cases or examples
4. Any relevant references or resources

### Pull Requests

We actively welcome pull requests:

1. Fork the repo
2. Create a branch from `main`
3. Make your changes
4. Ensure your code follows the project's style guide
5. Run tests if available
6. Create a pull request to `main`

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tutorx-mcp.git
   cd tutorx-mcp
   ```

2. Install dependencies:
   ```bash
   # Using uv (recommended)
   uv install

   # Or using pip
   pip install -e .
   ```

3. Run the server:
   ```bash
   python run.py --mode both
   ```

## Project Structure

- `main.py` - MCP server implementation
- `app.py` - Gradio interface
- `run.py` - Runner script
- `utils/` - Utility modules
  - `multimodal.py` - Multi-modal processing
  - `assessment.py` - Assessment functions
- `tools/` - Additional tools and utilities

## Adding New Features

When adding new features, please follow these guidelines:

1. For MCP tools and resources:
   - Add them to `main.py`
   - Use proper type hints and docstrings
   - Follow the existing pattern

2. For Gradio interface components:
   - Add them to `app.py`
   - Match the style of existing components
   - Ensure they interact properly with MCP tools

3. For utility functions:
   - Add them to appropriate files in `utils/`
   - Include proper documentation and tests

## Style Guide

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Include docstrings for all functions and classes
- Type hints are encouraged

## License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
