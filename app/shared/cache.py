from diskcache import Cache
from pathlib import Path

# Use a persistent directory (you can adjust this)
CACHE_DIR = Path(__file__).parent.parent.parent / ".cache"

# Create a singleton cache instance
cache = Cache(directory=str(CACHE_DIR))

def get_cache() -> Cache:
    return cache
