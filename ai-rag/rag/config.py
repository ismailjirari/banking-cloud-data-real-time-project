"""
Configuration loader for the AI Banking Data Assistant (RAG layer).

All secrets and connection details come from environment variables
(loaded from a local .env file). Nothing sensitive is hardcoded here.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # ---- Snowflake (Gold layer) ----
    SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
    SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
    SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
    SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
    SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "BANKING")
    SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "ANALYTICS")
    SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE")  # optional

    # ---- OpenRouter LLM ----
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    OPENROUTER_BASE_URL = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
    )

    # ---- Safety limits ----
    MAX_ROWS_RETURNED = int(os.getenv("MAX_ROWS_RETURNED", "50"))
    QUERY_TIMEOUT_SECONDS = int(os.getenv("QUERY_TIMEOUT_SECONDS", "30"))

    @classmethod
    def validate(cls):
        missing = []
        for key in [
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_USER",
            "SNOWFLAKE_PASSWORD",
            "SNOWFLAKE_WAREHOUSE",
            "OPENROUTER_API_KEY",
        ]:
            if not getattr(cls, key):
                missing.append(key)
        return missing
