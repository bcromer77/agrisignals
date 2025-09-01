import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "strategy.json"

def load_strategy_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

# Global strategy object
STRATEGY = load_strategy_config()

