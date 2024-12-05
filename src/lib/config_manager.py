import json
import os

class ConfigManager:
    def __init__(self, config_file="syncer_config.json"):
        self.config_file = config_file
        
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading config: {str(e)}")
            return {}
            
    def save_config(self, config):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {str(e)}")
            return False
