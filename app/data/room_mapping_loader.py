import json
from pathlib import Path
from config import ENVIRONMENT


if ENVIRONMENT == "development":
    ROOM_MAPPING_PATH = Path(__file__).parent / "room_mapping_dev.json"
else:
    ROOM_MAPPING_PATH = Path("/app/data/room_mapping_prod.json")

def load_room_mapping():
    with open(ROOM_MAPPING_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
