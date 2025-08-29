# D&D AI Conversation System

A Python application that facilitates interactive Dungeons & Dragons conversations between multiple AI characters and a human Dungeon Master (DM).

## Features

- **Multi-Character AI System**: Supports up to 4 AI characters, each with unique personalities and roles
- **Real-time Conversation**: Continuous conversation loop where AI characters respond to each other and the DM
- **Interactive Input**: Real-time user input handling with pause/resume functionality
- **Character Personalities**: Pre-defined D&D characters with distinct roles (Druid, Ranger, Fighter, Cleric)
- **Queue-based Messaging**: Each AI model maintains its own message queue for conversation context
- **Timeout Handling**: Automatic conversation termination after periods of inactivity

## Characters

The system includes four pre-configured D&D characters:

1. **Sapphira** (Kalina Eldaran) - Elf Druid: Wise, nature-connected, sometimes aloof
2. **Jasper** (Elrion Eldaran) - Elf Ranger: Skilled tracker, Kalina's brother, group scout
3. **Garnet** (Thrain Stonefist) - Dwarf Fighter: Brave, strong, honorable protector
4. **Ruby** (Lira Allaster) - Human Cleric: Compassionate, wise healer and moral compass

## Requirements

- Python 3.7+
- `httpx` library for HTTP requests
- Ollama API server running locally on port 11434
- `granite3.3:2b` model available in Ollama

## Installation

1. Install required dependencies:
```bash
pip install httpx
```

2. Ensure Ollama is installed and running:
```bash
# Start Ollama service
ollama serve
```

3. Pull the required model:
```bash
ollama pull granite3.3:2b
```

## Usage

### Basic Usage
```bash
python core.py
```

### Controls
- **Type messages**: Enter text and press Enter to send messages to all AI characters
- **ESC key**: Pause/resume the conversation
- **Ctrl+C**: Stop the conversation entirely

### Test Mode
The application includes a test mode that can be enabled by setting `GlobalFlags.test_mode = True` in the code.

## Configuration

### Endpoints
Modify the `OLLAMA_ENDPOINTS` dictionary to:
- Add/remove AI characters
- Change character descriptions and personalities
- Use different Ollama models

### Timeouts
- **Inactivity timeout**: 120 seconds (configurable in `llm_conversation()`)
- **Warning timeout**: 30 seconds before showing continuation prompt

### API Configuration
- **Base URL**: `http://localhost:11434` (default Ollama endpoint)
- **Timeout**: 15 seconds for HTTP requests

## Architecture

The application uses a multi-threaded architecture:

1. **Main Thread**: Handles user input and keyboard interactions
2. **Background Thread**: Manages the AI conversation loop
3. **Queue System**: Each AI character maintains a separate message queue
4. **Global State**: Shared flags for coordination between threads

## Message Flow

1. User types a message → Added to all character queues
2. Each AI character processes their queue → Generates response
3. Response is added to other characters' queues
4. Cycle continues until stopped or timeout

## Limitations

- Windows-specific keyboard input handling (`msvcrt`)
- Requires local Ollama installation
- Single model type support (granite3.3:2b)
- Limited error handling for network issues

## Troubleshooting

### Common Issues

1. **Connection Failed**: Ensure Ollama is running on `http://localhost:11434`
2. **Model Not Found**: Pull the `granite3.3:2b` model using `ollama pull granite3.3:2b`
3. **Keyboard Input Issues**: Application is designed for Windows PowerShell
4. **Timeout Errors**: Check network connectivity and Ollama service status

### Debug Output
The application provides debug messages prefixed with "DEBUG:" to help troubleshoot issues.

## License

This project is provided as-is for educational and experimental purposes.
