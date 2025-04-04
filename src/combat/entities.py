# Potential contents:
class CombatEntity:
    """Base class for entities that can participate in combat."""

    def __init__(self, name, health, attack, defense):
        self.name = name
        self.health = health
        self.max_health = health
        self.attack = attack
        self.defense = defense
        self.status_effects = []


class Player(CombatEntity):
    """Player character in combat."""

    def __init__(self, game_state):
        # Initialize from game state stats
        super().__init__("Player", 100, 10, 5)
        self.inventory = game_state.inventory
        self.equipped_weapon = None
        self.equipped_armor = None


class Enemy(CombatEntity):
    """Enemy character in combat."""

    def __init__(self, enemy_data):
        super().__init__(
            enemy_data["name"],
            enemy_data["health"],
            enemy_data["attack"],
            enemy_data["defense"],
        )
        self.type = enemy_data["type"]
        self.abilities = enemy_data.get("abilities", [])
        self.drops = enemy_data.get("drops", [])
