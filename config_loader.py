import json

class ConfigLoader:
    def __init__(self, config_path):
        self.config_path = config_path

    def load_config(self):
        """Load JSON configuration file."""
        try:
            with open(self.config_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file {self.config_path} not found.")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in {self.config_path}.")
