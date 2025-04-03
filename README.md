# GraphRAG Text Adventure Game

A text-based adventure game using Graph-based Retrieval-Augmented Generation to create a dynamic, responsive game world based on document content. The system includes flexible LLM integration, map generation, and an RPG-style combat system.

## Project Structure

```
graphrag-adventure/
├── src/
│   ├── document_processor.py       # Processes source documents to build knowledge graph
│   ├── enhanced_llm_game_engine.py # Main game engine with multiple LLM options
│   ├── map_generator.py           # Generates visual maps of the game world
│   ├── combat_system.py           # Handles RPG-style combat
│   └── local_llm_game_engine.py   # Simplified game engine for local LLMs only
├── data/
│   ├── documents/                 # Source Word documents go here
│   └── output/                    # Generated game data is stored here
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

## File Descriptions

### document_processor.py
Processes Word documents to extract text, entities, and relationships. It builds a knowledge graph that forms the foundation of the game world and breaks documents into chunks for retrieval.

Key functions:
- `extract_text_from_docx()`: Extracts text from Word documents
- `extract_entities_and_relations()`: Uses spaCy to identify entities and relationships
- `build_knowledge_graph()`: Creates a graph connecting entities via relationships
- `extract_game_elements()`: Derives game elements like locations, characters, items

### enhanced_llm_game_engine.py
The main game engine with support for multiple LLM providers. It handles game state management, text generation, and player actions.

Key components:
- `LLMManager`: Manages different LLM providers
- `GameState`: Tracks game state, including player location, inventory, NPC states, etc.
- `GraphRAGEngine`: Handles retrieval and generation using the knowledge graph

### map_generator.py
Creates visual maps of the game world and detailed maps of individual locations.

Key features:
- World map showing all discovered locations
- Detailed local maps with points of interest
- Map styling based on location types
- Visualization of connections between locations

### combat_system.py
Implements RPG-style combat mechanics.

Key features:
- Turn-based combat with stats and abilities
- Equipment system with weapons and armor
- Character progression with experience and levels
- Status effects and elemental damage

### local_llm_game_engine.py
A simplified version of the game engine that focuses specifically on local LLM integration.

## How to Play

### Setup

1. **Process your documents**:
   ```bash
   python src/document_processor.py --documents_dir data/documents --output_dir data/output
   ```

2. **Run the game**:
   ```bash
   python src/enhanced_llm_game_engine.py --game_data_dir data/output
   ```

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
- `cast [spell]`: Cast a spell (if known)
- `flee`: Attempt to escape

**System Commands:**
- `save`: Save your game
- `load`: Load a saved game
- `change llm`: Switch LLM provider
- `llm info`: Show LLM information
- `help`: Show available commands
- `quit`: Exit game

## Technical Details

### GraphRAG System

The game uses a Graph-based Retrieval-Augmented Generation approach:
1. It builds a knowledge graph connecting entities from source documents
2. When processing player commands, it retrieves relevant document chunks
3. The retrieved context plus game state is used to generate responses
4. The graph is dynamically updated based on player actions

### Dynamic World

The game world responds to player actions in several ways:
- NPC dispositions change based on interactions
- Faction standings update based on actions toward faction members
- The knowledge graph can be updated to reflect major world changes
- World events are recorded and influence future interactions

### Extension Points

The system is designed to be extensible in several ways:
- Add new LLM providers by implementing the `LLMProvider` interface
- Enhance the combat system with more abilities, status effects, etc.
- Expand map generation with more location types and features
- Add quest and dialogue systems building on the existing NPC state tracking

## Development History

This project was initially developed through an extended conversation with Claude in which we built features progressively:
1. Document processing pipeline
2. Basic GraphRAG game engine
3. Local LLM integration
4. Enhanced LLM provider system
5. Map generation
6. Combat system
7. Game integration

The modular design allows for continued development and enhancement of individual components while maintaining a coherent whole.
