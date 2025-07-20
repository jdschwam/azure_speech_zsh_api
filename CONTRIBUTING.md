# Contributing to Azure Speech API Script

We welcome contributions to the Azure Speech API Script! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues
- Use the GitHub Issues tab to report bugs or request features
- Provide detailed information about your environment (macOS version, zsh version, etc.)
- Include error messages and steps to reproduce issues

### Pull Requests
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly with different audio formats
5. Update documentation if needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Setup
1. Clone the repository
2. Install dependencies: `brew install jq ffmpeg`
3. Set up Azure Speech Services credentials
4. Test with: `./azure_speech_v1.sh debug`

### Code Style
- Follow existing zsh scripting conventions
- Use meaningful variable names
- Add comments for complex logic
- Maintain compatibility with macOS zsh

### Testing
- Test with various audio formats (MP3, WAV, FLAC, etc.)
- Verify both TTS and STT functionality
- Test error handling and edge cases
- Ensure file naming conventions work correctly

## Feature Requests
We're always looking to improve! Some areas for potential contributions:
- Additional audio format support
- Batch processing capabilities
- Integration with other services
- Performance optimizations
- Enhanced error handling

## Questions?
Feel free to open an issue for questions or start a discussion.

Thank you for contributing! 🎤
