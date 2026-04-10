import os
import yaml
from dotenv import load_dotenv

from chat_engine.core.utils.patterns import Singleton

ROOT_FOLDER = os.getcwd()


class ConfigManager(metaclass=Singleton):
    def __init__(self):
        self._config_dict = {}
        
        config_folder_path = os.path.dirname(__file__)
        config_path = os.path.join(config_folder_path, "application.yaml")
        self._load_configs(config_path)

    def _load_configs(self, config_path: str):
        # Load configurations from the config file
        with open(config_path, "r") as file:
            loaded_configs = yaml.safe_load(file)
            self._config_dict = loaded_configs

        # Load/override configs from .env file
        load_dotenv(os.path.join(ROOT_FOLDER, ".env"))
        for key, value in os.environ.items():
            self._config_dict[key] = value

    def get_config(self, key: str, default=None):
        return self._config_dict.get(key, default)