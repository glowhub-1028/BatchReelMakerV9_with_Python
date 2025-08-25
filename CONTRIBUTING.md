# Contributing to BatchReelMaker V9

Thank you for your interest in contributing to BatchReelMaker V9! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Development Setup

1. **Run the application** to test your changes:
   ```bash
   python app.py
   ```

2. **Test the build process**:
   ```bash
   python build_exe.py
   ```

## Making Changes

### Code Style
- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and reasonably sized

### Testing
- Test your changes thoroughly before submitting
- Ensure the application runs without errors
- Test with different file formats and sizes
- Verify memory usage doesn't cause issues

### Commit Messages
Use clear, descriptive commit messages:
- Start with a verb (Add, Fix, Update, etc.)
- Keep the first line under 50 characters
- Add more details in the body if needed

Example:
```
Add memory optimization for large images

- Limit base image size to 1920x1920 pixels
- Add garbage collection during processing
- Optimize video export settings
```

## Submitting Changes

1. **Create a feature branch** from main:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit them

3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request** on GitHub

## Pull Request Guidelines

- **Describe the changes** clearly in the PR description
- **Include screenshots** if UI changes are made
- **Test thoroughly** before submitting
- **Update documentation** if needed

## Areas for Contribution

### Features
- Additional video effects
- More audio format support
- Batch processing improvements
- UI/UX enhancements

### Bug Fixes
- Memory optimization
- Performance improvements
- Cross-platform compatibility
- Error handling

### Documentation
- Code comments
- User guides
- API documentation
- Tutorial videos

## Questions?

If you have questions about contributing, feel free to:
- Open an issue on GitHub
- Ask in the discussions section
- Contact the maintainers

Thank you for contributing to BatchReelMaker V9!
