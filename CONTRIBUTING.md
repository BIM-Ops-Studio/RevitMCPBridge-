# Contributing to RevitMCPBridge

Thank you for your interest in contributing to RevitMCPBridge!

## How to Contribute

### Reporting Issues
- Use GitHub Issues to report bugs
- Include Revit version, error messages, and steps to reproduce
- Screenshots or logs are helpful

### Suggesting Features
- Open an issue with the "enhancement" label
- Describe the use case and proposed solution
- Check existing issues first to avoid duplicates

### Pull Requests
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Test with Revit 2025 and/or 2026
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

### Code Style
- Follow existing patterns in the codebase
- Use meaningful variable and method names
- Add XML documentation for public methods
- Keep methods focused and reasonably sized

### Testing
- Test your changes with a live Revit instance
- Verify MCP communication works
- Check for memory leaks on long-running operations

## Development Setup

1. Install Visual Studio 2022
2. Install Revit 2025 or 2026
3. Clone the repository
4. Open the `.csproj` file
5. Build in Release mode
6. Deploy DLL to Revit Addins folder

## Questions?

- Open an issue for questions
- Email: weberg@bimopsstudio.com
- Web: [BIM Ops Studio](https://bimopsstudio.com)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
