import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from infrastructure.db.session import Base, engine
from infrastructure.db.models.user_model import UserModel

Base.metadata.create_all(bind=engine)
print("✅ Database initialized.")
