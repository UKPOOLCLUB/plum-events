from dotenv import load_dotenv
import os

load_dotenv()
print("TEST: DATABASE_URL =", os.environ.get("DATABASE_URL"))