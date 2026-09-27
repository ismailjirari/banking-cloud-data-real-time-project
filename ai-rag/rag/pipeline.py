"""
Orchestrates the full RAG flow:

  question -> Text-to-SQL (LLM) -> Snowflake Gold retrieval
            -> grounded-answer generation (LLM) -> answer + transparency data
"""

from dataclasses import dataclass, field

from . import llm, retriever, sql_generator
from .prompts import ANSWER_SYSTEM_PROMPT, NO_ANSWER_MESSAGE


@dataclass
class RAGResult:
    answer: str
    sql: str | None = None
    columns: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    source_tables: list[str] = field(default_factory=list)
    error: str | None = None


def _extract_tables(sql: str) -> list[str]:
    tables = []
    for name in ("DIM_CUSTOMERS", "DIM_ACCOUNTS", "FACT_TRANSACTIONS"):
        if name in sql.upper():
            tables.append(name)
    return tables


def answer_question(question: str) -> RAGResult:
    # 1. Question understanding + Text-to-SQL
    try:
        sql = sql_generator.generate_sql(question)
    except sql_generator.SQLGenerationError as exc:
        return RAGResult(answer=NO_ANSWER_MESSAGE, error=str(exc))
    except llm.LLMError as exc:
        return RAGResult(answer="The AI assistant is temporarily unavailable.", error=str(exc))

    if sql is None:
        return RAGResult(answer=NO_ANSWER_MESSAGE)

    # 2. Retrieve from Gold layer
    try:
        columns, rows = retriever.run_query(sql)
    except retriever.RetrievalError as exc:
        return RAGResult(
            answer="I couldn't retrieve data from the Gold layer to answer that.",
            sql=sql,
            error=str(exc),
        )

    context_text = retriever.rows_to_context_text(columns, rows)

    # 3. Grounded answer generation
    user_prompt = (
        f"User question: {question}\n\n"
        f"Retrieved data (from Snowflake Gold layer):\n{context_text}"
    )
    try:
        answer = llm.chat(ANSWER_SYSTEM_PROMPT, user_prompt)
    except llm.LLMError as exc:
        return RAGResult(
            answer="The AI assistant is temporarily unavailable.",
            sql=sql,
            columns=columns,
            rows=rows,
            source_tables=_extract_tables(sql),
            error=str(exc),
        )

    return RAGResult(
        answer=answer,
        sql=sql,
        columns=columns,
        rows=rows,
        source_tables=_extract_tables(sql),
    )
