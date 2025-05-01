# AI-Powered Map Generator

This tool generates detailed, interconnected maps for game worlds using AI-powered text generation. It uses your knowledge graph and structured data to create rich, coherent game environments that players can explore.

## Features

- Generates hierarchical map areas with rich descriptions
- Creates interconnected network of locations
- Populates areas with NPCs, items, and environmental details
- Maintains spatial coherence with coordinate system
- Visualizes the generated map as a network graph
- Saves generated maps for persistence

## Prerequisites

- Python 3.8+
- Required packages: NetworkX, Matplotlib, pandas
- Knowledge graph in GEXF format
- Entity and relation data in CSV format (optional but recommended)

## Usage

### Basic Usage

To generate a map for a specific location:

```bash
./test_map_generator.py "The Ironroot Range"
```

### Advanced Options

```bash
./test_map_generator.py "The Skyways" --data-dir data/output/elyria --provider anthropic --model claude-3-opus-20240229 --verbose --visualize
```

Parameters:
- `location`: The name of the location to generate a map for
- `--data-dir`: Directory containing knowledge graph and related data files (default: "data/output/elyria")
- `--provider`: LLM provider to use (choices: "anthropic", "openai", "google", "rule_based", default: "anthropic")
- `--model`: Specific LLM model to use (if not specified, uses provider default)
- `--verbose`: Print detailed progress information
- `--visualize`: Visualize the map after generation
- `--noisy`: Print LLM response time information (by default, these are suppressed)

### Visualizing an Existing Map

If you've already generated a map and want to visualize it:

```bash
./test_map_visualizer.py --map-file data/output/elyria/maps/map_data.json --output map_visualization.png
```

Parameters:
- `--map-file`: Path to the map data file (default: "data/output/elyria/maps/map_data.json")
- `--output`: Path to save the visualization image (optional)
- `--no-show`: Don't display the plot interactively

## File Structure

Maps are saved in the specified output directory under a `maps` subdirectory:
- `map_data.json`: Contains all generated map areas and their connections

## Map Visualization

The map visualization shows:
- Nodes representing map areas (main entrances are highlighted)
- Directed edges showing connections between areas
- Labels for area names and sub-locations
- Direction labels on edges

## Example

```bash
# Generate a map for The Abyssal Realm using the OpenAI provider
./test_map_generator.py "The Abyssal Realm" --provider openai --model gpt-4 --visualize

# Generate a more detailed map with verbose output
./test_map_generator.py "TreeHome" --verbose --visualize
```

## Notes

- The first generation may take some time as the LLM creates detailed area descriptions
- Each run will either create new areas or expand existing ones if the map already exists
- You can set map generation depth to control how many layers of areas are created
- Areas are interconnected with proper directional exits (north/south, east/west, up/down)