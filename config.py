"""
Shared configuration constants for Voice2Justice.

All modules should import DB_PATH from here rather than computing
their own paths — ensures every layer of the app points to the same file.
"""
import os
from dotenv import load_dotenv

# Load .env — idempotent; subsequent calls from blueprints are no-ops
load_dotenv()

# Absolute path to the SQLite database (lives in the flask/ directory)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'complaints.db')
