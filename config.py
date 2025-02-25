from pathlib import Path
import os
import yaml
from connexion import FlaskApp


def load_config():
    config_path = Path("config.yaml")
    if not config_path.exists():
        return {
            "iam": {
                "provider_type": "testing",
                "iamaas": {
                    "introspect_url": "https://iamaas.example.com/introspect"
                },
                "aconnect": {
                    "auth_url": "https://aconnect.example.com/auth"
                }
            }
        }

    with open(config_path) as f:
        return yaml.safe_load(f)



class ConnexionWrapper:
    def __init__(self, config):
        self.config = config
        self.connexion_app = FlaskApp(__name__)