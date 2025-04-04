import json
import os
from typing import Dict, Any, Optional

# Import dotenv for environment variable loading
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not found. Install with 'pip install python-dotenv' to use .env files.")

DEFAULT_CONFIG = {
    "output": {
        "use_color": True,
        "delay": 0.02,
        "width": 80
    },
    "llm": {
        "default_provider": "rule_based",
        "temperature": 0.7,
        "max_tokens": 500
    },
    "game": {
        "autosave": True,
        "autosave_turns": 10,
        "save_dir": "saves"
    }
}

def load_environment_variables(env_file: str = ".env") -> bool:
    """
    Load environment variables from .env file.

    Args:
        env_file: Path to .env file

    Returns:
        Boolean indicating success
    """
    if not DOTENV_AVAILABLE:
        return False

    if os.path.exists(env_file):
        try:
            load_dotenv(env_file)
            print(f"Loaded environment variables from {env_file}")
            return True
        except Exception as e:
            print(f"Error loading environment variables: {e}")
            return False
    else:
        print(f"Environment file {env_file} not found")
        return False

def get_api_key(provider_name: str) -> Optional[str]:
    """
    Get API key for a specific provider.

    Args:
        provider_name: Name of the provider (anthropic, openai, google)

    Returns:
        API key if found, None otherwise
    """
    # Map of provider names to environment variable names
    env_var_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY"
    }

    if provider_name.lower() in env_var_map:
        env_var = env_var_map[provider_name.lower()]
        return os.environ.get(env_var)

    return None

def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file, falling back to defaults.

    Args:
        config_file: Path to configuration file (optional)

    Returns:
        Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()

    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)

            # Merge user config into defaults
            for section, values in user_config.items():
                if section in config:
                    config[section].update(values)
                else:
                    config[section] = values
        except Exception as e:
            print(f"Error loading config file: {e}")

    return config

def save_config(config: Dict[str, Any], config_file: str) -> bool:
    """
    Save configuration to file.

    Args:
        config: Configuration dictionary
        config_file: Path to save configuration

    Returns:
        Boolean indicating success
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(config_file)), exist_ok=True)

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
