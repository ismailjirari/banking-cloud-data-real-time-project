"""
Executes validated read-only SQL against the Snowflake Gold layer and
returns the results in a form easy to hand to the LLM and to the UI.
"""

import snowflake.connector

from .config import Config


class RetrievalError(Exception):
    pass


def _get_connection():
    if not all(
        [
            Config.SNOWFLAKE_ACCOUNT,
            Config.SNOWFLAKE_USER,
            Config.SNOWFLAKE_PASSWORD,
            Config.SNOWFLAKE_WAREHOUSE,
        ]
    ):
        raise RetrievalError(
            "Snowflake credentials are not fully configured. Check your .env file."
        )

    return snowflake.connector.connect(
        account=Config.SNOWFLAKE_ACCOUNT,
        user=Config.SNOWFLAKE_USER,
        password=Config.SNOWFLAKE_PASSWORD,
        warehouse=Config.SNOWFLAKE_WAREHOUSE,
        database=Config.SNOWFLAKE_DATABASE,
        schema=Config.SNOWFLAKE_SCHEMA,
        role=Config.SNOWFLAKE_ROLE or None,
        login_timeout=Config.QUERY_TIMEOUT_SECONDS,
    )


def run_query(sql: str) -> tuple[list[str], list[tuple]]:
    """
    Executes a read-only SQL query and returns (column_names, rows).
    Rows are capped defensively even if the generated SQL's own LIMIT
    was larger than expected.
    """
    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(sql)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchmany(Config.MAX_ROWS_RETURNED)
        return columns, rows
    except Exception as exc:
        raise RetrievalError(f"Query execution failed: {exc}") from exc
    finally:
        if conn is not None:
            conn.close()


def rows_to_context_text(columns: list[str], rows: list[tuple], max_rows: int = 20) -> str:
    """Formats retrieved rows into a compact text block for the LLM prompt."""
    if not rows:
        return "No rows returned."

    lines = [" | ".join(columns)]
    for row in rows[:max_rows]:
        lines.append(" | ".join(str(v) for v in row))

    extra = len(rows) - max_rows
    if extra > 0:
        lines.append(f"... ({extra} more rows not shown)")

    return "\n".join(lines)
