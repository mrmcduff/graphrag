import os
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Tuple, Optional, Set, Any
import math
import random
import tempfile

class MapStyle:
    """Class to define the visual style of the map."""

    def __init__(self):
        # Base colors
        self.background_color = (245, 240, 231)  # Parchment-like background
        self.unexplored_color = (200, 200, 200)  # Light gray for unexplored areas
        self.border_color = (101, 67, 33)  # Brown border
        self.text_color = (30, 30, 30)  # Dark gray text

        # Location type colors
        self.location_colors = {
            "default": (120, 120, 120),  # Default gray
            "town": (210, 180, 140),  # Tan for towns/settlements
            "forest": (34, 139, 34),  # Forest green
            "mountain": (139, 137, 137),  # Mountain gray
            "water": (65, 105, 225),  # Water blue
            "dungeon": (139, 69, 19),  # Dungeon brown
            "castle": (128, 0, 0),  # Castle red
            "cave": (105, 105, 105),  # Cave dark gray
            "temple": (218, 165, 32),  # Temple gold
            "ruins": (169, 169, 169),  # Ruins gray
            "special": (148, 0, 211)  # Special location purple
        }

        # Path colors
        self.path_color = (101, 67, 33)  # Path brown
        self.special_path_color = (184, 134, 11)  # Special path gold

        # Node sizes
        self.default_node_size = 300
        self.current_location_size = 500
        self.important_location_size = 400

        # Font settings
        self.font_color = (0, 0, 0)
        self.font_path = None  # Will try to find a system font
        self.title_font_size = 24
        self.location_font_size = 12
        self.legend_font_size = 14

        # Map decorations
        self.show_compass = True
        self.add_parchment_texture = True
        self.add_map_border = True
        self.show_legend = True

class MapGenerator:
    """Class to generate maps for the text adventure game."""

    def __init__(self, game_state):
        """
        Initialize the map generator.

        Args:
            game_state: The current game state
        """
        self.game_state = game_state
        self.map_style = MapStyle()
        self.font = self._load_font()
        self.title_font = self._load_font(size=self.map_style.title_font_size)
        self.location_font = self._load_font(size=self.map_style.location_font_size)
        self.legend_font = self._load_font(size=self.map_style.legend_font_size)

        # Location type mapping
        self.location_types = self._derive_location_types()

        # Cached map layouts
        self.cached_layouts = {}

    def _load_font(self, size=12):
        """Load a font for the map."""
        try:
            # Try to load the specified font
            if self.map_style.font_path and os.path.exists(self.map_style.font_path):
                return ImageFont.truetype(self.map_style.font_path, size)

            # Try common system fonts
            system_fonts = [
                # Linux fonts
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
                "/usr/share/fonts/TTF/DejaVuSerif.ttf",
                # macOS fonts
                "/Library/Fonts/Times New Roman.ttf",
                "/System/Library/Fonts/Times.ttc",
                # Windows fonts
                "C:\\Windows\\Fonts\\times.ttf",
                "C:\\Windows\\Fonts\\arial.ttf"
            ]

            for font_path in system_fonts:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)

            # Fallback to default
            return ImageFont.load_default()

        except Exception as e:
            print(f"Error loading font: {e}")
            return ImageFont.load_default()

    def _derive_location_types(self) -> Dict[str, str]:
        """
        Derive location types from location names and graph relations.

        Returns:
            Dictionary mapping location names to their types
        """
        location_types = {}

        # Analyze location names to guess types
        for location in self.game_state.locations:
            location_lower = location.lower()

            # Check for type keywords in name
            if any(word in location_lower for word in ["town", "village", "city", "settlement", "outpost"]):
                location_types[location] = "town"
            elif any(word in location_lower for word in ["forest", "woods", "grove", "jungle"]):
                location_types[location] = "forest"
            elif any(word in location_lower for word in ["mountain", "peak", "hill", "cliff"]):
                location_types[location] = "mountain"
            elif any(word in location_lower for word in ["lake", "river", "ocean", "sea", "pond", "stream"]):
                location_types[location] = "water"
            elif any(word in location_lower for word in ["dungeon", "prison", "jail"]):
                location_types[location] = "dungeon"
            elif any(word in location_lower for word in ["castle", "fort", "fortress", "citadel", "palace"]):
                location_types[location] = "castle"
            elif any(word in location_lower for word in ["cave", "cavern", "grotto"]):
                location_types[location] = "cave"
            elif any(word in location_lower for word in ["temple", "shrine", "sanctuary", "altar"]):
                location_types[location] = "temple"
            elif any(word in location_lower for word in ["ruin", "ruins", "ancient", "abandoned"]):
                location_types[location] = "ruins"
            else:
                location_types[location] = "default"

        # Enhance with data from relations
        location_relations = self.game_state.relations_df.loc[
            self.game_state.relations_df['predicate'].isin(['is_a', 'type_of', 'contains'])
        ]

        for _, relation in location_relations.iterrows():
            subject = relation['subject']
            object_ = relation['object']

            # If subject is a location we know
            if subject in location_types:
                # Check if object describes a type
                for type_name, keywords in [
                    ("town", ["town", "village", "city", "settlement"]),
                    ("forest", ["forest", "woods", "grove"]),
                    ("mountain", ["mountain", "peak", "hill"]),
                    ("water", ["lake", "river", "ocean", "sea"]),
                    ("dungeon", ["dungeon", "prison"]),
                    ("castle", ["castle", "fort", "fortress"]),
                    ("cave", ["cave", "cavern"]),
                    ("temple", ["temple", "shrine", "sanctuary"]),
                    ("ruins", ["ruin", "ruins", "ancient"])
                ]:
                    if any(keyword in object_.lower() for keyword in keywords):
                        location_types[subject] = type_name
                        break

        return location_types

    def _get_location_color(self, location: str, is_current: bool = False, is_visited: bool = False) -> Tuple[int, int, int]:
        """Get the appropriate color for a location based on its type and status."""
        # Current location is highlighted differently
        if is_current:
            # Return a slightly brighter version of the location type color
            location_type = self.location_types.get(location, "default")
            base_color = self.map_style.location_colors.get(location_type, self.map_style.location_colors["default"])
            # Make it 20% brighter (but cap at 255 for each channel)
            return tuple(min(255, int(c * 1.2)) for c in base_color)

        # Unexplored locations
        if not is_visited:
            return self.map_style.unexplored_color

        # Regular location with a known type
        location_type = self.location_types.get(location, "default")
        return self.map_style.location_colors.get(location_type, self.map_style.location_colors["default"])

    def get_node_positions(self, graph: nx.Graph, focus_node: str, available_nodes: Set[str]) -> Dict[str, Tuple[float, float]]:
        """
        Get the positions for nodes in the map, focusing on a central node.

        Args:
            graph: The graph of locations
            focus_node: The location to focus on (usually current player location)
            available_nodes: Set of nodes to include in the layout

        Returns:
            Dictionary mapping node names to (x, y) positions
        """
        # Check if we have a cached layout
        cache_key = f"{focus_node}_{len(available_nodes)}"
        if cache_key in self.cached_layouts:
            return self.cached_layouts[cache_key]

        # Create a subgraph of available nodes
        subgraph = graph.subgraph(available_nodes)

        # Get a spring layout centered on the focus node
        pos = nx.spring_layout(
            subgraph,
            k=0.3,  # Optimal distance between nodes
            iterations=100,  # More iterations for better layout
            seed=42  # Consistent layout between runs
        )

        # If focus node exists, center the layout on it
        if focus_node in pos:
            focus_pos = pos[focus_node]
            # Shift all positions so focus_node is at (0, 0)
            for node in pos:
                pos[node] = (pos[node][0] - focus_pos[0], pos[node][1] - focus_pos[1])

        # Cache the layout
        self.cached_layouts[cache_key] = pos
        return pos

    def generate_map(self, current_location: str, output_path: str = None, width: int = 800, height: int = 600) -> str:
        """
        Generate a map visualization centered on the current location.

        Args:
            current_location: The current player location
            output_path: Path to save the map image (optional)
            width: Width of the map in pixels
            height: Height of the map in pixels

        Returns:
            Path to the generated map file
        """
        # Create a new image
        img = Image.new('RGB', (width, height), self.map_style.background_color)
        draw = ImageDraw.Draw(img)

        # Add parchment texture effect if enabled
        if self.map_style.add_parchment_texture:
            self._add_parchment_texture(img, width, height)

        # Add a title
        title = "Map of the Realm"
        title_width, title_height = draw.textsize(title, font=self.title_font)
        draw.text(
            ((width - title_width) // 2, 20),
            title,
            fill=self.map_style.text_color,
            font=self.title_font
        )

        # Determine which locations to show on the map
        visited_locations = set(self.game_state.visited_locations)
        connected_to_visited = set()

        # Add locations connected to visited locations
        for location in visited_locations:
            location_info = self._get_location_info(location)
            connected_to_visited.update(location_info["connected_locations"])

        # Combine all locations to show
        map_locations = visited_locations.union(connected_to_visited)

        # If current location isn't in our data, add it
        if current_location not in map_locations:
            map_locations.add(current_location)
            visited_locations.add(current_location)

        # Get a subgraph of the locations to show
        graph = self.game_state.graph.copy()

        # Get positions for nodes
        pos = self.get_node_positions(graph, current_location, map_locations)

        # Scale positions to fit the image
        margin = 50  # Margin in pixels
        scaled_pos = {}

        if pos:
            # Find min and max positions
            min_x = min(p[0] for p in pos.values())
            max_x = max(p[0] for p in pos.values())
            min_y = min(p[1] for p in pos.values())
            max_y = max(p[1] for p in pos.values())

            # Calculate scaling factors
            x_scale = (width - 2 * margin) / (max_x - min_x) if max_x > min_x else 1
            y_scale = (height - 2 * margin) / (max_y - min_y) if max_y > min_y else 1
            scale = min(x_scale, y_scale)

            # Scale and shift positions to center in the image
            for node, position in pos.items():
                x = margin + (position[0] - min_x) * scale
                y = margin + (position[1] - min_y) * scale
                scaled_pos[node] = (x, y)

        # Draw edges between locations
        for source in map_locations:
            source_id = source.lower().replace(' ', '_')
            if source_id in graph.nodes:
                for target in graph.neighbors(source_id):
                    target_name = graph.nodes[target].get('label', target)
                    if target_name in map_locations:
                        # Only draw if both nodes are in our map view
                        if source in scaled_pos and target_name in scaled_pos:
                            start = scaled_pos[source]
                            end = scaled_pos[target_name]
                            # Draw the edge
                            draw.line([start, end], fill=self.map_style.path_color, width=2)

        # Draw nodes for each location
        for location in map_locations:
            if location in scaled_pos:
                position = scaled_pos[location]

                # Determine node attributes
                is_current = location == current_location
                is_visited = location in visited_locations

                # Get node size
                node_size = self.map_style.default_node_size
                if is_current:
                    node_size = self.map_style.current_location_size
                elif is_visited:
                    node_size = self.map_style.important_location_size

                # Calculate radius and bounding box
                radius = math.sqrt(node_size) / 2
                x, y = position
                bbox = (x - radius, y - radius, x + radius, y + radius)

                # Get node color
                color = self._get_location_color(location, is_current, is_visited)

                # Draw the node
                draw.ellipse(bbox, fill=color, outline=self.map_style.border_color)

                # Add a special marker for current location
                if is_current:
                    inner_radius = radius * 0.6
                    inner_bbox = (x - inner_radius, y - inner_radius, x + inner_radius, y + inner_radius)
                    draw.ellipse(inner_bbox, fill=(255, 255, 255), outline=self.map_style.border_color)

                # Add location label
                label_width, label_height = draw.textsize(location, font=self.location_font)
                label_position = (x - label_width / 2, y + radius + 5)
                draw.text(label_position, location, fill=self.map_style.text_color, font=self.location_font)

        # Add a compass rose
        if self.map_style.show_compass:
            self._add_compass_rose(draw, width - 80, 80, 30)

        # Add a legend
        if self.map_style.show_legend:
            self._add_legend(draw, 50, height - 150)

        # Add a decorative border
        if self.map_style.add_map_border:
            self._add_map_border(draw, width, height)

        # Save the image to a temporary file if no output path is provided
        if not output_path:
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, "game_map.png")

        img.save(output_path)
        return output_path

    def _get_location_info(self, location: str) -> Dict[str, Any]:
        """Get information about a location."""
        if hasattr(self.game_state, '_get_location_info'):
            return self.game_state._get_location_info(location)

        # Fallback implementation if game_state doesn't have the method
        location_id = location.lower().replace(' ', '_')

        # Get connected locations
        connected_locations = []
        if location_id in self.game_state.graph.nodes:
            for neighbor in self.game_state.graph.neighbors(location_id):
                node_data = self.game_state.graph.nodes[neighbor]
                if 'label' in node_data:
                    connected_locations.append(node_data['label'])

        return {
            "name": location,
            "connected_locations": connected_locations
        }

    def _add_parchment_texture(self, img, width, height):
        """Add a parchment-like texture to the background."""
        pixels = img.load()

        for y in range(height):
            for x in range(width):
                # Get current pixel color
                r, g, b = pixels[x, y]

                # Add some noise to create texture
                noise = random.randint(-7, 7)

                # Apply noise to each channel, keeping within valid range
                r = max(0, min(255, r + noise))
                g = max(0, min(255, g + noise))
                b = max(0, min(255, b + noise))

                # Set the pixel
                pixels[x, y] = (r, g, b)

        # Add some "age spots" for that old map look
        for _ in range(width * height // 10000):  # Number of spots based on map size
            spot_x = random.randint(0, width - 1)
            spot_y = random.randint(0, height - 1)
            spot_size = random.randint(5, 20)
            spot_color = (
                random.randint(180, 220),
                random.randint(160, 200),
                random.randint(120, 170)
            )

            draw = ImageDraw.Draw(img)
            bbox = (
                spot_x - spot_size // 2,
                spot_y - spot_size // 2,
                spot_x + spot_size // 2,
                spot_y + spot_size // 2
            )
            draw.ellipse(bbox, fill=spot_color)

    def _add_compass_rose(self, draw, x, y, size):
        """Add a compass rose to the map."""
        # Draw circle
        draw.ellipse((x - size, y - size, x + size, y + size),
                     outline=self.map_style.border_color,
                     fill=(255, 255, 255, 128))

        # Draw cardinal directions
        # North
        draw.line((x, y - size // 2, x, y - size), fill=self.map_style.border_color, width=2)
        draw.text((x - 5, y - size - 15), "N", fill=self.map_style.text_color, font=self.location_font)

        # South
        draw.line((x, y + size // 2, x, y + size), fill=self.map_style.border_color, width=2)
        draw.text((x - 5, y + size + 5), "S", fill=self.map_style.text_color, font=self.location_font)

        # East
        draw.line((x + size // 2, y, x + size, y), fill=self.map_style.border_color, width=2)
        draw.text((x + size + 5, y - 5), "E", fill=self.map_style.text_color, font=self.location_font)

        # West
        draw.line((x - size // 2, y, x - size, y), fill=self.map_style.border_color, width=2)
        draw.text((x - size - 15, y - 5), "W", fill=self.map_style.text_color, font=self.location_font)

    def _add_legend(self, draw, x, y):
        """Add a legend to the map."""
        legend_items = [
            ("Current Location", (255, 255, 255)),  # White center dot
            ("Visited Location", self.map_style.location_colors["default"]),
            ("Unexplored Location", self.map_style.unexplored_color),
            ("Town", self.map_style.location_colors["town"]),
            ("Forest", self.map_style.location_colors["forest"]),
            ("Mountain", self.map_style.location_colors["mountain"]),
            ("Water", self.map_style.location_colors["water"]),
            ("Castle", self.map_style.location_colors["castle"]),
            ("Temple", self.map_style.location_colors["temple"]),
            ("Dungeon", self.map_style.location_colors["dungeon"])
        ]

        # Draw legend title
        draw.text((x, y), "Legend", fill=self.map_style.text_color, font=self.legend_font)

        # Draw legend items
        for i, (label, color) in enumerate(legend_items):
            y_pos = y + 25 + i * 20

            # Draw color sample
            draw.rectangle((x, y_pos, x + 15, y_pos + 15), fill=color, outline=self.map_style.border_color)

            # Draw label
            draw.text((x + 25, y_pos), label, fill=self.map_style.text_color, font=self.legend_font)

    def _add_map_border(self, draw, width, height):
        """Add a decorative border to the map."""
        border_width = 10

        # Draw outer rectangle
        draw.rectangle(
            [border_width/2, border_width/2, width - border_width/2, height - border_width/2],
            outline=self.map_style.border_color,
            width=border_width
        )

        # Add corner decorations
        corner_size = 20

        # Top-left corner
        draw.line((border_width, border_width + corner_size, border_width + corner_size, border_width),
                  fill=self.map_style.border_color, width=2)

        # Top-right corner
        draw.line((width - border_width - corner_size, border_width, width - border_width, border_width + corner_size),
                  fill=self.map_style.border_color, width=2)

        # Bottom-left corner
        draw.line((border_width, height - border_width - corner_size, border_width + corner_size, height - border_width),
                  fill=self.map_style.border_color, width=2)

        # Bottom-right corner
        draw.line((width - border_width - corner_size, height - border_width, width - border_width, height - border_width - corner_size),
                  fill=self.map_style.border_color, width=2)

        # Draw midpoint markers on the border
        marker_size = 5

        # Top middle
        draw.rectangle((width/2 - marker_size, border_width - marker_size,
                         width/2 + marker_size, border_width + marker_size),
                        fill=self.map_style.border_color)

        # Bottom middle
        draw.rectangle((width/2 - marker_size, height - border_width - marker_size,
                         width/2 + marker_size, height - border_width + marker_size),
                        fill=self.map_style.border_color)

        # Left middle
        draw.rectangle((border_width - marker_size, height/2 - marker_size,
                         border_width + marker_size, height/2 + marker_size),
                        fill=self.map_style.border_color)

        # Right middle
        draw.rectangle((width - border_width - marker_size, height/2 - marker_size,
                         width - border_width + marker_size, height/2 + marker_size),
                        fill=self.map_style.border_color)

    def generate_zoomed_map(self, current_location: str, output_path: str = None, width: int = 800, height: int = 600) -> str:
        """
        Generate a detailed map of the current location and its immediate surroundings.

        Args:
            current_location: The current player location
            output_path: Path to save the map image (optional)
            width: Width of the map in pixels
            height: Height of the map in pixels

        Returns:
            Path to the generated map file
        """
        # Create a new image
        img = Image.new('RGB', (width, height), self.map_style.background_color)
        draw = ImageDraw.Draw(img)

        # Add parchment texture effect if enabled
        if self.map_style.add_parchment_texture:
            self._add_parchment_texture(img, width, height)

        # Add a title
        title = f"{current_location} and Surroundings"
        title_width, title_height = draw.textsize(title, font=self.title_font)
        draw.text(
            ((width - title_width) // 2, 20),
            title,
            fill=self.map_style.text_color,
            font=self.title_font
        )

        # Get information about the current location
        location_info = self._get_location_info(current_location)

        # Determine location type and style accordingly
        location_type = self.location_types.get(current_location, "default")

        # Draw the detailed local map based on location type
        if location_type == "town":
            self._draw_town_map(draw, width, height, current_location, location_info)
        elif location_type == "forest":
            self._draw_forest_map(draw, width, height, current_location, location_info)
        elif location_type == "mountain":
            self._draw_mountain_map(draw, width, height, current_location, location_info)
        elif location_type == "water":
            self._draw_water_map(draw, width, height, current_location, location_info)
        elif location_type == "dungeon":
            self._draw_dungeon_map(draw, width, height, current_location, location_info)
        elif location_type == "castle":
            self._draw_castle_map(draw, width, height, current_location, location_info)
        elif location_type == "cave":
            self._draw_cave_map(draw, width, height, current_location, location_info)
        elif location_type == "temple":
            self._draw_temple_map(draw, width, height, current_location, location_info)
        elif location_type == "ruins":
            self._draw_ruins_map(draw, width, height, current_location, location_info)
        else:
            self._draw_generic_map(draw, width, height, current_location, location_info)

        # Add a compass rose
        if self.map_style.show_compass:
            self._add_compass_rose(draw, width - 80, 80, 30)

        # Add a decorative border
        if self.map_style.add_map_border:
            self._add_map_border(draw, width, height)

        # Save the image to a temporary file if no output path is provided
        if not output_path:
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, "location_map.png")

        img.save(output_path)
        return output_path

    def _draw_town_map(self, draw, width, height, location_name, location_info):
        """Draw a detailed map for a town location."""
        center_x, center_y = width // 2, height // 2

        # Draw town boundary
        town_radius = min(width, height) // 3
        draw.ellipse(
            (center_x - town_radius, center_y - town_radius,
             center_x + town_radius, center_y + town_radius),
            outline=self.map_style.border_color,
            width=2
        )

        # Draw main roads
        road_color = (139, 115, 85)  # Brown
        road_width = 8

        # Horizontal main road
        draw.line(
            (center_x - town_radius, center_y, center_x + town_radius, center_y),
            fill=road_color,
            width=road_width
        )

        # Vertical main road
        draw.line(
            (center_x, center_y - town_radius, center_x, center_y + town_radius),
            fill=road_color,
            width=road_width
        )

        # Draw buildings
        building_color = (160, 82, 45)  # Sienna
        num_buildings = random.randint(10, 20)

        for _ in range(num_buildings):
            # Randomly position within town limits
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, town_radius * 0.8)
            bx = center_x + distance * math.cos(angle)
            by = center_y + distance * math.sin(angle)

            # Random building size
            building_size = random.randint(10, 25)

            # Draw building
            draw.rectangle(
                (bx - building_size // 2, by - building_size // 2,
                 bx + building_size // 2, by + building_size // 2),
                fill=building_color,
                outline=(0, 0, 0)
            )

        # Draw special building at center (town hall, etc.)
        special_building_color = (139, 69, 19)  # Saddle brown
        special_size = 35

        draw.rectangle(
            (center_x - special_size // 2, center_y - special_size // 2,
             center_x + special_size // 2, center_y + special_size // 2),
            fill=special_building_color,
            outline=(0, 0, 0),
            width=2
        )

        # Add a label for the town center
        center_label = "Town Square"
        label_width, label_height = draw.textsize(center_label, font=self.location_font)
        draw.text(
            (center_x - label_width // 2, center_y + special_size // 2 + 5),
            center_label,
            fill=self.map_style.text_color,
            font=self.location_font
        )

        # Draw paths to connected locations
        for connected in location_info.get("connected_locations", []):
            # Calculate angle based on connected location name (deterministic but seems random)
            # This ensures consistent positioning of connections
            name_hash = sum(ord(c) for c in connected) % 360
            angle = math.radians(name_hash)

            # Draw path from town edge to map edge
            edge_x = center_x + town_radius * math.cos(angle)
            edge_y = center_y + town_radius * math.sin(angle)

            # Extend to border of map
            border_dist = max(width, height)
            border_x = center_x + border_dist * math.cos(angle)
            border_y = center_y + border_dist * math.sin(angle)

            # Draw the path
            draw.line(
                (edge_x, edge_y, border_x, border_y),
                fill=self.map_style.path_color,
                width=3
            )

            # Add a label for the connected location
            label_dist = town_radius * 1.2
            label_x = center_x + label_dist * math.cos(angle)
            label_y = center_y + label_dist * math.sin(angle)

            # Adjust label position for readability
            label_width, label_height = draw.textsize(connected, font=self.location_font)
            label_x -= label_width // 2
            label_y -= label_height // 2

            # Draw a small background for the text
            text_bg_padding = 3
            draw.rectangle(
                (label_x - text_bg_padding, label_y - text_bg_padding,
                 label_x + label_width + text_bg_padding, label_y + label_height + text_bg_padding),
                fill=(255, 255, 255, 180),
                outline=self.map_style.border_color
            )

            draw.text(
                (label_x, label_y),
                connected,
                fill=self.map_style.text_color,
                font=self.location_font
            )

            # Add a small arrow indicating direction
            arrow_dist = town_radius * 1.1
            arrow_x = center_x + arrow_dist * math.cos(angle)
            arrow_y = center_y + arrow_dist * math.sin(angle)
            arrow_size = 8

            # Draw arrow
            arrow_points = [
                (arrow_x, arrow_y),
                (arrow_x - arrow_size * math.cos(angle + math.pi/4),
                 arrow_y - arrow_size * math.sin(angle + math.pi/4)),
                (arrow_x - arrow_size * math.cos(angle - math.pi/4),
                 arrow_y - arrow_size * math.sin(angle - math.pi/4))
            ]
            draw.polygon(arrow_points, fill=self.map_style.path_color)

    def _draw_forest_map(self, draw, width, height, location_name, location_info):
        """Draw a detailed map for a forest location."""
        center_x, center_y = width // 2, height // 2

        # Draw forest background
        forest_radius = min(width, height) // 3
        background_color = (220, 240, 220)  # Light green

        draw.ellipse(
            (center_x - forest_radius, center_y - forest_radius,
             center_x + forest_radius, center_y + forest_radius),
            fill=background_color,
            outline=(34, 139, 34),  # Forest green
            width=2
        )

        # Draw trees
        tree_colors = [(0, 100, 0), (34, 139, 34), (0, 128, 0)]  # Dark green variations
        num_trees = random.randint(30, 50)

        for _ in range(num_trees):
            # Randomly position within forest limits
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, forest_radius * 0.9)
            tx = center_x + distance * math.cos(angle)
            ty = center_y + distance * math.sin(angle)

            # Random tree size
            tree_size = random.randint(5, 15)

            # Draw tree trunk (brown rectangle)
            trunk_width = max(2, tree_size // 3)
            trunk_height = tree_size // 2
            draw.rectangle(
                (tx - trunk_width // 2, ty - trunk_height // 2,
                 tx + trunk_width // 2, ty + trunk_height // 2),
                fill=(139, 69, 19)  # Brown
            )

            # Draw tree top (green circle)
            tree_color = random.choice(tree_colors)
            draw.ellipse(
                (tx - tree_size, ty - tree_size - trunk_height // 2,
                 tx + tree_size, ty + tree_size - trunk_height // 2),
                fill=tree_color
            )

        # Draw a clearing at the center
        clearing_radius = forest_radius // 4
        draw.ellipse(
            (center_x - clearing_radius, center_y - clearing_radius,
             center_x + clearing_radius, center_y + clearing_radius),
            fill=(144, 238, 144),  # Light green
            outline=(34, 139, 34),  # Forest green
            width=1
        )

        # Add a label for the clearing
        clearing_label = "Forest Clearing"
        label_width, label_height = draw.textsize(clearing_label, font=self.location_font)
        draw.text(
            (center_x - label_width // 2, center_y - label_height // 2),
            clearing_label,
            fill=self.map_style.text_color,
            font=self.location_font
        )

        # Draw paths to connected locations
        self._draw_location_connections(draw, center_x, center_y, forest_radius, location_info, width, height)

    def _draw_mountain_map(self, draw, width, height, location_name, location_info):
        """Draw a detailed map for a mountain location."""
        center_x, center_y = width // 2, height // 2

        # Draw mountain background
        mountain_radius = min(width, height) // 3
        background_color = (200, 200, 200)  # Gray

        draw.ellipse(
            (center_x - mountain_radius, center_y - mountain_radius,
             center_x + mountain_radius, center_y + mountain_radius),
            fill=background_color,
            outline=(105, 105, 105),  # Dark gray
            width=2
        )

        # Draw mountain peaks
        num_peaks = random.randint(5, 10)
        peak_colors = [(139, 137, 137), (105, 105, 105), (169, 169, 169)]  # Gray variations

        for i in range(num_peaks):
            # Position peaks in a roughly circular pattern
            angle = i * (2 * math.pi / num_peaks) + random.uniform(-0.3, 0.3)
            distance = random.uniform(mountain_radius * 0.3, mountain_radius * 0.8)
            px = center_x + distance * math.cos(angle)
            py = center_y + distance * math.sin(angle)

            # Random peak size
            peak_size = random.randint(20, 40)
            peak_color = random.choice(peak_colors)

            # Draw triangular peak
            draw.polygon(
                [(px, py - peak_size),
                 (px - peak_size // 2, py + peak_size // 2),
                 (px + peak_size // 2, py + peak_size // 2)],
                fill=peak_color,
                outline=(0, 0, 0)
            )

            # Add snow cap to some peaks
            if random.random() > 0.5:
                snow_size = peak_size // 3
                draw.polygon(
                    [(px, py - peak_size),
                     (px - snow_size // 2, py - peak_size + snow_size),
                     (px + snow_size // 2, py - peak_size + snow_size)],
                    fill=(255, 255, 255)  # White
                )

        # Draw a plateau at the center
        plateau_radius = mountain_radius // 4
        draw.ellipse(
            (center_x - plateau_radius, center_y - plateau_radius,
             center_x + plateau_radius, center_y + plateau_radius),
            fill=(160, 160, 160),  # Light gray
            outline=(105, 105, 105),  # Dark gray
            width=1
        )

        # Add a label for the plateau
        plateau_label = "Mountain Pass"
        label_width, label_height = draw.textsize(plateau_label, font=self.location_font)
        draw.text(
            (center_x - label_width // 2, center_y - label_height // 2),
            plateau_label,
            fill=self.map_style.text_color,
            font=self.location_font
        )

        # Draw paths to connected locations
        self._draw_location_connections(draw, center_x, center_y, mountain_radius, location_info, width, height)

    def _draw_water_map(self, draw, width, height, location_name, location_info):
        """Draw a detailed map for a water location."""
        center_x, center_y = width // 2, height // 2

        # Draw water background
        water_radius = min(width, height) // 3
        water_color = (65, 105, 225)  # Royal blue

        draw.ellipse(
            (center_x - water_radius, center_y - water_radius,
             center_x + water_radius, center_y + water_radius),
            fill=water_color,
            outline=(25, 25, 112),  # Midnight blue
            width=2
        )

        # Draw wave patterns
        num_waves = 20
        wave_color = (135, 206, 250)  # Light sky blue

        for i in range(num_waves):
            # Randomly position waves
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, water_radius * 0.8)
            wx = center_x + distance * math.cos(angle)
            wy = center_y + distance * math.sin(angle)

            # Random wave size
            wave_size = random.randint(5, 15)

            # Draw a curved wave line
            points = []
            for j in range(5):
                points.append((
                    wx + (j - 2) * wave_size // 2,
                    wy + math.sin(j * math.pi / 2) * wave_size // 2
                ))

            draw.line(points, fill=wave_color, width=2)

        # Draw a small island or boat at the center
        is_island = random.choice([True, False])

        if is_island:
            # Draw a small island
            island_radius = water_radius // 5
            island_color = (210, 180, 140)  # Tan

            draw.ellipse(
                (center_x - island_radius, center_y - island_radius,
                 center_x + island_radius, center_y + island_radius),
                fill=island_color,
                outline=(139, 69, 19)  # Brown
            )

            # Add a palm tree
            tree_height = island_radius * 1.5
            draw.line(
                (center_x, center_y, center_x, center_y - tree_height),
                fill=(139, 69, 19),  # Brown
                width=3
            )

            # Draw palm leaves
            leaf_size = island_radius // 2
            for i in range(5):
                angle = i * (2 * math.pi / 5)
                leaf_x = center_x + math.cos(angle) * leaf_size
                leaf_y = center_y - tree_height + math.sin(angle) * leaf_size
                draw.line(
                    (center_x, center_y - tree_height, leaf_x, leaf_y),
                    fill=(0, 128, 0),  # Green
                    width=2
                )

            # Add a label
            island_label = "Small Island"
            label_width, label_height = draw.textsize(island_label, font=self.location_font)
            draw.text(
                (center_x - label_width // 2, center_y + island_radius + 5),
                island_label,
                fill=self.map_style.text_color,
                font=self.location_font
            )
        else:
            # Draw a boat
            boat_width = water_radius // 3
            boat_height = boat_width // 2
            boat_color = (139, 69, 19)  # Brown

            # Draw boat hull
            draw.rectangle(
                (center_x - boat_width // 2, center_y - boat_height // 3,
                 center_x + boat_width // 2, center_y + boat_height // 3),
                fill=boat_color,
                outline=(0, 0, 0)
            )

            # Draw sail
            sail_height = boat_height * 1.5
            draw.polygon(
                [(center_x, center_y - sail_height),
                 (center_x, center_y - boat_height // 3),
                 (center_x + boat_width // 3, center_y - boat_height // 3)],
                fill=(255, 255, 255),  # White
                outline=(0, 0, 0)
            )

            # Add a label
            boat_label = "Your Boat"
            label_width, label_height = draw.textsize(boat_label, font=self.location_font)
            draw.text(
                (center_x - label_width // 2, center_y + boat_height // 2 + 5),
                boat_label,
                fill=self.map_style.text_color,
                font=self.location_font
            )

        # Draw paths (docks or bridges) to connected locations
        self._draw_location_connections(draw, center_x, center_y, water_radius, location_info, width, height,
                                       path_width=4, path_color=(139, 69, 19))  # Brown docks/bridges

    def _draw_dungeon_map(self, draw, width, height, location_name, location_info):
        """Draw a detailed map for a dungeon location."""
        center_x, center_y = width // 2, height // 2

        # Draw dungeon background (darker to represent indoor)
        dungeon_width = min(width, height) // 2
        dungeon_height = dungeon_width * 3 // 4
        background_color = (50, 50, 50)  # Dark gray

        # Draw dungeon outline
        draw.rectangle(
            (center_x - dungeon_width // 2, center_y - dungeon_height // 2,
             center_x + dungeon_width // 2, center_y + dungeon_height // 2),
            fill=background_color,
            outline=(0, 0, 0),
            width=3
        )

        # Draw dungeon rooms and corridors
        room_color = (80, 80, 80)  # Slightly lighter gray
        num_rooms = random.randint(5, 8)
        rooms = []

        # Generate rooms
        for _ in range(num_rooms):
            room_width = random.randint(dungeon_width // 8, dungeon_width // 4)
            room_height = random.randint(dungeon_height // 8, dungeon_height // 4)

            # Position within dungeon
            room_x = center_x + random.randint(-dungeon_width // 3, dungeon_width // 3)
            room_y = center_y + random.randint(-dungeon_height // 3, dungeon_height // 3)

            # Save room
            rooms.append((room_x, room_y, room_width, room_height))

            # Draw room
            draw.rectangle(
                (room_x - room_width // 2, room_y - room_height // 2,
                 room_x + room_width // 2, room_y + room_height // 2),
                fill=room_color,
                outline=(0, 0, 0)
            )

        # Draw corridors between rooms
        for i in range(len(rooms) - 1):
            room1_x, room1_y, _, _ = rooms[i]
            room2_x, room2_y, _, _ = rooms[i + 1]

            # Draw corridor
            corridor_width = 4

            # First horizontal then vertical (L-shaped corridor)
            draw.rectangle(
                (room1_x - corridor_width // 2, room1_y - corridor_width // 2,
                 room2_x + corridor_width // 2, room1_y + corridor_width // 2),
                fill=room_color,
                outline=None
            )

            draw.rectangle(
                (room2_x - corridor_width // 2, room1_y - corridor_width // 2,
                 room2_x + corridor_width // 2, room2_y + corridor_width // 2),
                fill=room_color,
                outline=None
            )

        # Draw entrance/exit at the bottom
        entrance_width = dungeon_width // 8
        entrance_height = dungeon_height // 10
        draw.rectangle(
            (center_x - entrance_width // 2, center_y + dungeon_height // 2 - entrance_height,
             center_x + entrance_width // 2, center_y + dungeon_height // 2),
            fill=(0, 0, 0),
            outline=(139, 69, 19),
            width=2
        )

        # Add a label for the entrance
        entrance_label = "Entrance"
        label_width, label_height = draw.textsize(entrance_label, font=self.location_font)
        draw.text(
            (center_x - label_width // 2, center_y + dungeon_height // 2 + 5),
            entrance_label,
            fill=self.map_style.text_color,
            font=self.location_font
        )

        # Mark current position with an X
        current_x = center_x
        current_y = center_y
        marker_size = 10
        draw.line(
            (current_x - marker_size, current_y - marker_size,
             current_x + marker_size, current_y + marker_size),
            fill=(255, 0, 0),
            width=2
        )
        draw.line(
            (current_x - marker_size, current_y + marker_size,
             current_x + marker_size, current_y - marker_size),
            fill=(255, 0, 0),
            width=2
        )

        # Add "You are here" label
        here_label = "You are here"
        label_width, label_height = draw.textsize(here_label, font=self.location_font)
        draw.text(
            (current_x - label_width // 2, current_y + marker_size + 5),
            here_label,
            fill=(255, 0, 0),
            font=self.location_font
        )

        # Draw paths to connected locations outside the dungeon
        self._draw_location_connections(
            draw, center_x, center_y + dungeon_height // 2, 0,
            location_info, width, height, start_from_edge=True
        )

    def _draw_generic_map(self, draw, width, height, location_name, location_info):
        """Draw a generic map for any location type."""
        center_x, center_y = width // 2, height // 2

        # Draw a simple circular area for the current location
        location_radius = min(width, height) // 4
        location_color = self._get_location_color(location_name, is_current=True)

        draw.ellipse(
            (center_x - location_radius, center_y - location_radius,
             center_x + location_radius, center_y + location_radius),
            fill=location_color,
            outline=self.map_style.border_color,
            width=2
        )

        # Add location name at center
        label_width, label_height = draw.textsize(location_name, font=self.title_font)
        draw.text(
            (center_x - label_width // 2, center_y - label_height // 2),
            location_name,
            fill=self.map_style.text_color,
            font=self.title_font
        )

        # Draw paths to connected locations
        self._draw_location_connections(draw, center_x, center_y, location_radius, location_info, width, height)

    def _draw_castle_map(self, draw, width, height, location_name, location_info):
        """Draw a detailed map for a castle location."""
        center_x, center_y = width // 2, height // 2

        # Draw castle outline
        castle_width = min(width, height) // 3
        castle_height = castle_width
        wall_color = (139, 69, 19)  # Brown

        # Draw main castle walls (square)
        draw.rectangle(
            (center_x - castle_width // 2, center_y - castle_height // 2,
             center_x + castle_width // 2, center_y + castle_height // 2),
            fill=(200, 200, 200),  # Light gray
            outline=wall_color,
            width=3
        )

        # Draw corner towers
        tower_size = castle_width // 6
        tower_positions = [
            (center_x - castle_width // 2, center_y - castle_height // 2),  # Top-left
            (center_x + castle_width // 2, center_y - castle_height // 2),  # Top-right
            (center_x - castle_width // 2, center_y + castle_height // 2),  # Bottom-left
            (center_x + castle_width // 2, center_y + castle_height // 2)   # Bottom-right
        ]

        for tx, ty in tower_positions:
            draw.ellipse(
                (tx - tower_size, ty - tower_size, tx + tower_size, ty + tower_size),
                fill=(150, 150, 150),  # Gray
                outline=wall_color,
                width=2
            )

        # Draw central keep
        keep_size = castle_width // 3
        draw.rectangle(
            (center_x - keep_size // 2, center_y - keep_size // 2,
             center_x + keep_size // 2, center_y + keep_size // 2),
            fill=(100, 100, 100),  # Dark gray
            outline=(0, 0, 0),
            width=2
        )

        # Draw keep roof (triangle)
        roof_height = keep_size // 2
        draw.polygon(
            [(center_x - keep_size // 2, center_y - keep_size // 2),
             (center_x + keep_size // 2, center_y - keep_size // 2),
             (center_x, center_y - keep_size // 2 - roof_height)],
            fill=(139, 0, 0),  # Dark red
            outline=(0, 0, 0)
        )

        # Draw castle gate
        gate_width = castle_width // 8
        gate_height = castle_height // 6
        draw.rectangle(
            (center_x - gate_width // 2, center_y + castle_height // 2 - gate_height,
             center_x + gate_width // 2, center_y + castle_height // 2),
            fill=(0, 0, 0),
            outline=wall_color,
            width=2
        )

        # Add a label for the keep
        keep_label = "Main Keep"
        label_width, label_height = draw.textsize(keep_label, font=self.location_font)
        draw.text(
            (center_x - label_width // 2, center_y + 5),
            keep_label,
            fill=self.map_style.text_color,
            font=self.location_font
        )

        # Add a label for the gate
        gate_label = "Main Gate"
        label_width, label_height = draw.textsize(gate_label, font=self.location_font)
        draw.text(
            (center_x - label_width // 2, center_y + castle_height // 2 + 5),
            gate_label,
            fill=self.map_style.text_color,
            font=self.location_font
        )

        # Draw paths to connected locations from the gate
        self._draw_location_connections(
            draw, center_x, center_y + castle_height // 2, 0,
            location_info, width, height, start_from_edge=True
        )

    def _draw_location_connections(self, draw, center_x, center_y, radius, location_info,
                                  width, height, path_width=3, path_color=None, start_from_edge=False):
        """Helper method to draw connections to other locations."""
        if not path_color:
            path_color = self.map_style.path_color

        for connected in location_info.get("connected_locations", []):
            # Calculate angle based on connected location name (deterministic but seems random)
            name_hash = sum(ord(c) for c in connected) % 360
            angle = math.radians(name_hash)

            # Draw path from location edge to map edge
            if start_from_edge:
                # Start directly from center, useful for buildings
                start_x, start_y = center_x, center_y
            else:
                start_x = center_x + radius * math.cos(angle)
                start_y = center_y + radius * math.sin(angle)

            # Extend to border of map
            border_dist = max(width, height)
            border_x = center_x + border_dist * math.cos(angle)
            border_y = center_y + border_dist * math.sin(angle)

            # Draw the path
            draw.line(
                (start_x, start_y, border_x, border_y),
                fill=path_color,
                width=path_width
            )

            # Add a label for the connected location
            label_dist = radius * 1.2 if radius > 0 else 50
            label_x = center_x + label_dist * math.cos(angle)
            label_y = center_y + label_dist * math.sin(angle)

            # Adjust label position for readability
            label_width, label_height = draw.textsize(connected, font=self.location_font)
            label_x -= label_width // 2
            label_y -= label_height // 2

            # Draw a small background for the text
            text_bg_padding = 3
            draw.rectangle(
                (label_x - text_bg_padding, label_y - text_bg_padding,
                 label_x + label_width + text_bg_padding, label_y + label_height + text_bg_padding),
                fill=(255, 255, 255, 180),
                outline=self.map_style.border_color
            )

            draw.text(
                (label_x, label_y),
                connected,
                fill=self.map_style.text_color,
                font=self.location_font
            )
