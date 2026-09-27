"""
Turns a natural-language question into a safe, read-only SQL query against
the Snowflake Gold layer (BANKING.ANALYTICS).
"""

import re

from . import llm
from .prompts import SQL_SYSTEM_PROMPT

ALLOWED_TABLES = {
    "BANKING.ANALYTICS.DIM_CUSTOMERS",
    "BANKING.ANALYTICS.DIM_ACCOUNTS",
    "BANKING.ANALYTICS.FACT_TRANSACTIONS",
}

FORBIDDEN_KEYWORDS = (
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "MERGE",
    "TRUNCATE", "GRANT", "REVOKE", "CALL", "COPY", "PUT", "UNLOAD",
)


class SQLGenerationError(Exception):
    pass


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```sql", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^```", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def _validate_sql(sql: str) -> None:
    upper = sql.upper()

    if not upper.strip().startswith("SELECT") and not upper.strip().startswith("WITH"):
        raise SQLGenerationError("Generated query is not a SELECT statement.")

    for kw in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{kw}\b", upper):
            raise SQLGenerationError(f"Generated query contains forbidden keyword: {kw}")

    if ";" in sql.strip().rstrip(";"):
        raise SQLGenerationError("Multiple statements are not allowed.")

    if not any(table in upper for table in ALLOWED_TABLES):
        raise SQLGenerationError("Generated query does not reference an allowed Gold table.")

    if "LIMIT" not in upper:
        raise SQLGenerationError("Generated query is missing a LIMIT clause.")


def generate_sql(question: str) -> str | None:
    """
    Returns a validated SQL SELECT string, or None if the question cannot be
    answered from the Gold layer (LLM returns NO_SQL) or fails validation.
    """
    raw = llm.chat(SQL_SYSTEM_PROMPT, question)
    raw = _strip_code_fences(raw)

    if raw.strip().upper() == "NO_SQL" or raw.strip() == "":
        return None

    try:
        _validate_sql(raw)
    except SQLGenerationError:
        # Fail safe: treat an invalid/unsafe query as "cannot answer"
        return None

    return raw.rstrip(";")
