import json
from pathlib import Path

ROOM_MAPPING_PATH = Path(__file__).parent / "room_mapping.json"

def load_room_mapping():
    with open(ROOM_MAPPING_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
