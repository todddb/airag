# Contributing to AI RAG

Thank you for your interest in contributing!

## Ways to Contribute

- 🐛 Report bugs
- ✨ Suggest features
- 📖 Improve documentation
- 🔧 Submit pull requests
- 💬 Help others in discussions

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Test thoroughly
6. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/airag.git
cd airag

# Setup for development
./tools/setup.sh --dev

# Start dev mode (hot reload)
./tools/dev.sh start
```

## Code Style

- **Python**: Follow PEP 8
- **JavaScript**: Use ES6+
- **Bash**: Use ShellCheck
- **Comments**: Explain why, not what

## Testing

```bash
# Run endpoint tests
./tools/test-endpoints.sh

# Test specific service
curl http://localhost:8000/health
```

## Pull Request Process

1. Update documentation
2. Add tests if applicable
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Questions? Open a [Discussion](https://github.com/yourusername/airag/discussions)
