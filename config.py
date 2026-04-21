import os
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8192"))
COMPANY_NAME = os.getenv("COMPANY_NAME", "CROID")
