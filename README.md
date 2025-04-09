# GraphRAG Text Adventure Game

A text-based adventure game using Graph-based Retrieval-Augmented Generation to create a dynamic, responsive game world based on document content. The system includes flexible LLM integration, robust game state management, and an RPG-style combat system.

## New Architecture Overview

The project has been completely restructured into a modular architecture that separates concerns while maintaining all original functionality. The new architecture provides:

- A robust game loop structure
- Clean separation of components
- Enhanced error handling
- Improved integration between modules
- Maintainable, extensible codebase

## Project Structure

```
graphrag-adventure/
├── src/
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── game_loop.py          # Main game loop implementation
│   │   ├── command_processor.py  # Process and execute player commands
│   │   └── output_manager.py     # Handle game output formatting
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── llm_manager.py        # Manages LLM providers
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # LLMProvider base class
│   │   │   ├── local_api.py      # Local API LLM provider
│   │   │   ├── local_direct.py   # Direct model LLM provider
│   │   │   ├── openai.py         # OpenAI LLM provider
│   │   │   ├── anthropic.py      # Anthropic LLM provider
│   │   │   ├── google.py         # Google LLM provider
│   │   │   └── rule_based.py     # Fallback rule-based provider
│   ├── gamestate/
│   │   ├── __init__.py
│   │   ├── game_state.py         # Game state management
│   │   └── world.py              # World state management
│   ├── graphrag/
│   │   ├── __init__.py
│   │   ├── graph_rag_engine.py   # GraphRAG implementation
│   │   └── retrieval.py          # Context retrieval functions
│   ├── combat/
│   │   ├── __init__.py
│   │   ├── combat_system.py      # Main combat system
│   │   └── entities.py           # Combat entity classes
│   ├── util/
│   │   ├── __init__.py
│   │   └── config.py             # Configuration utilities
│   ├── document_processor.py     # Processes source documents to build knowledge graph
│   ├── map_generator.py          # Generates visual maps of the game world
│   └── main.py                   # Entry point
├── data/
│   ├── documents/                # Source documents
│   └── output/                   # Generated game data
└── requirements.txt
```

## Environment Requirements

The project requires Python 3.10 or later. Key dependencies include:

```
pandas
python-docx
spacy (with en_core_web_md or en_core_web_lg model)
networkx
matplotlib
pillow
requests
```

For local LLM support (optional):

```
llama-cpp-python or ctransformers
```

## Component Descriptions

### Engine Module

#### game_loop.py

The central coordinator that manages the game's execution flow. It initializes all required components, handles player input, processes commands, and generates appropriate responses. The game loop also manages state transitions and ensures proper integration between components.

#### command_processor.py

Parses and processes player commands, determining the appropriate action based on the command type. It supports various command categories including movement, interaction, inventory management, combat, and system commands.

#### output_manager.py

Handles the formatting and display of game output with features like text wrapping, color coding, and typing effects. It provides consistent presentation of different types of messages (narrative, system, error).

### LLM Module

#### llm_manager.py

Manages different LLM providers through a unified interface. It handles provider creation, selection, and fallback mechanisms to ensure reliable text generation.

#### providers/

Contains implementations for different LLM backends:

- **base.py**: Defines the base LLMProvider class and LLMType enum
- **rule_based.py**: A fallback provider that generates responses without an LLM
- **local_api.py**: Connects to a local LLM server (e.g., llama.cpp)
- **local_direct.py**: Directly loads local models (e.g., via llama-cpp-python)
- **openai.py**: Uses OpenAI's API
- **anthropic.py**: Uses Anthropic's API
- **google.py**: Uses Google's Gemini API

### GameState Module

#### game_state.py

Maintains the complete state of the game world including player location, inventory, NPC states, factions, and world events. It loads game data from processed documents and provides methods for updating the state based on player actions.

### GraphRAG Module

#### graph_rag_engine.py

Implements the Graph-based Retrieval-Augmented Generation system that powers the game's response generation. It retrieves relevant context from the knowledge graph and document chunks, then generates appropriate responses using the active LLM provider.

### Combat Module

#### combat_system.py

Handles combat mechanics including turn-based combat, stats, abilities, status effects, and equipment. It integrates with the game state to reflect combat outcomes in the world.

### Document Processing

#### document_processor.py

Processes source documents to extract entities, relationships, and text chunks that form the foundation of the game world. It builds a knowledge graph connecting all elements of the game world.

### Map Generation

#### map_generator.py

Creates visual representations of the game world, including world maps showing all discovered locations and detailed local maps.

## How to Play

### Setup

1. **Process your documents**:

   ```bash
   python src/document_processor.py --documents_dir data/documents --output_dir data/output
   ```

2. **Run the game**:
   ```bash
   python src/main.py --game_data_dir data/output
   ```

### Command-Line Options

When starting the game, you can use these command-line options:

- `--game_data_dir PATH`: Directory containing game data files (default: data/output)
- `--load_save PATH`: Load a previously saved game file
- `--no_color`: Disable colored output
- `--no_typing_effect`: Disable typing effect for text display
- `--width NUM`: Width of the text display (default: 80)

### LLM Configuration

When starting the game, you'll be prompted to select an LLM provider:

1. Local API (e.g., llama.cpp server)
2. Local direct model loading
3. OpenAI
4. Anthropic Claude
5. Google Gemini
6. Rule-based (no LLM)

If choosing a cloud provider (3-5), you'll need to provide an API key.

### Game Commands

**Basic Navigation:**

- `look`: Examine surroundings
- `go [location]`: Move to a connected location
- `talk [character]`: Talk to a character
- `take [item]`: Pick up an item
- `use [item]`: Use an item from inventory
- `inventory`: Check your items

**Map Commands:**

- `map`: Show world map
- `local map`: Show detailed map of current location

**Combat Commands:**

- `attack [enemy]`: Start combat with an enemy
- `stats`: Show your character stats
- `equip [item]`: Equip weapon or armor

During combat:

- `attack`: Basic attack
- `block`: Defensive stance
- `dodge`: Evasive maneuver
- `use [item]`: Use an item
- `flee`: Attempt to escape

**System Commands:**

- `save`: Save your game
- `load`: Load a saved game
- `llm info`: Show LLM information
- `llm change`: Switch LLM provider
- `help`: Show available commands
- `quit`: Exit game

## Technical Details

### GraphRAG System

The game uses a Graph-based Retrieval-Augmented Generation approach:

1. It builds a knowledge graph connecting entities from source documents
2. When processing player commands, it retrieves relevant document chunks
3. The retrieved context plus game state is used to generate responses
4. The graph is dynamically updated based on player actions

### Game Loop Architecture

The game loop follows this execution flow:

1. Initialize all components (LLM, game state, GraphRAG engine, combat system)
2. Display welcome message and initial location description
3. Enter main loop:
   - Get player input
   - Process command via CommandProcessor
   - Display result via OutputManager
   - Handle state changes
   - Repeat until exit

### Dynamic World

The game world responds to player actions in several ways:

- NPC dispositions change based on interactions
- Faction standings update based on actions toward faction members
- The knowledge graph can be updated to reflect major world changes
- World events are recorded and influence future interactions

### Design Patterns

The architecture uses several design patterns:

- **Dependency Injection**: Components receive their dependencies through constructors
- **Strategy Pattern**: LLM providers implement a common interface, making them interchangeable
- **Facade Pattern**: The GameLoop presents a simplified interface to complex subsystems
- **Command Pattern**: The CommandProcessor encapsulates commands as objects
- **Observer Pattern (implicit)**: State changes trigger appropriate responses in other components

## API Server

The game can also be run as an API server, allowing you to interact with it programmatically or build custom frontends.

### Setup

1. **Install additional dependencies**:
   ```bash
   pip install flask flask-cors
   ```
   Or update using the provided requirements.txt:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the API server**:
   ```bash
   python -m src.api.server --host 0.0.0.0 --port 8000 --debug
   ```

   Command-line options:
   - `--host`: Host to bind the server to (default: 0.0.0.0)
   - `--port`: Port to run the server on (default: 8000)
   - `--debug`: Run in debug mode (not recommended for production)
   - `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

3. **Test the API**:
   - Use the included command-line client:
     ```bash
     python -m src.client.api_client
     ```
   - Open the web client in a browser:
     ```bash
     open src/client/web_client.html
     ```
   - Use the automated test suite:
     ```bash
     python -m src.api.test_api
     ```

### API Endpoints

- `POST /api/game/new`: Create a new game session
- `POST /api/game/<session_id>/command`: Process a command
- `POST /api/game/<session_id>/save`: Save game state
- `POST /api/game/<session_id>/load`: Load game state
- `GET /api/game/<session_id>/state`: Get current game state
- `POST /api/game/<session_id>/llm`: Set LLM provider
- `DELETE /api/game/<session_id>`: End game session

### Response Format

API responses include formatted content with metadata for display:

```json
{
  "success": true,
  "message": "Command processed successfully",
  "content": [
    {
      "text": "You find yourself in a dark forest.",
      "format": "location",
      "color": "#33a1ff"
    },
    {
      "text": "You see a mysterious figure in the distance.",
      "format": "normal"
    }
  ],
  "metadata": {
    "action_type": "movement",
    "combat_active": false,
    "player_location": "Dark Forest",
    "inventory_count": 3,
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## Extension Points

The system is designed to be extensible in several ways:

- Add new LLM providers by implementing the `LLMProvider` interface
- Enhance the combat system with more abilities, status effects, etc.
- Expand map generation with more location types and features
- Add quest and dialogue systems building on the existing NPC state tracking
- Implement additional command types in the CommandProcessor
- Create custom frontends using the API server

## Development History

This project was initially developed through conversations with AI assistants. The current architecture represents a significant restructuring of the original codebase to improve modularity, maintainability, and expandability while preserving all original functionality.
