# 🤖 AI Banking Data Assistant (RAG on the Gold Layer)

A small, self-contained AI layer added on top of the existing
**PostgreSQL → Kafka/Debezium → MinIO → Airflow → Snowflake → dbt** pipeline.
It does not modify the existing pipeline, DAGs, dbt models, or CI/CD in any way —
it only *reads* from the Snowflake Gold layer.

## Architecture

```text
User
  ↓
Streamlit Chatbot UI (app.py)
  ↓
Text-to-SQL (LLM via OpenRouter) — question -> constrained SQL SELECT
  ↓
Snowflake Gold layer (BANKING.ANALYTICS: dim_customers, dim_accounts, fact_transactions)
  ↓
Retrieved rows / aggregates
  ↓
Grounded answer generation (LLM via OpenRouter)
  ↓
Natural-language answer + transparency panel (SQL + retrieved rows)
```

This is a lightweight **Text-to-SQL RAG** pattern adapted for structured/tabular
data, not a document-RAG system: there is no vector database, because the
"knowledge base" is the Gold layer itself.

## Gold tables used

- `BANKING.ANALYTICS.DIM_CUSTOMERS` (SCD2 customer dimension)
- `BANKING.ANALYTICS.DIM_ACCOUNTS` (SCD2 account dimension)
- `BANKING.ANALYTICS.FACT_TRANSACTIONS` (transaction fact table)

These are the actual tables produced by `banking_dbt/models/marts`.

## Model choice

Default model: `openai/gpt-4o-mini` via OpenRouter — fast, inexpensive, and
reliable enough for constrained SQL generation and short grounded summaries.
Swap models anytime via the `OPENROUTER_MODEL` env var, e.g.
`anthropic/claude-3.5-haiku` or `google/gemini-2.0-flash-001`.

## Setup

```bash
cd ai-rag
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env
# then edit .env with your real Snowflake + OpenRouter credentials
```

`.env` is already covered by the repo's root `.gitignore` — never commit it.

## Run

```bash
cd ai-rag
streamlit run app.py
```

Then open the URL Streamlit prints (default `http://localhost:8501`).

## Example questions to demo

- "How many customers are there?"
- "What is the total transaction volume?"
- "Which customers have the highest transaction activity?"
- "What is the total balance across all accounts?"
- "Which accounts had the most transactions?"
- "Give me a short summary of the current banking activity."
- "What's the weather in Casablanca?" → should be refused (not in Gold layer)

## Safety notes

- Only `SELECT` queries are ever executed; the generator is instructed to
  respond `NO_SQL` for out-of-scope questions, and generated SQL is validated
  (no DDL/DML keywords, only the three Gold tables, `LIMIT` enforced) before
  it is ever run against Snowflake.
- For a real deployment, point `SNOWFLAKE_USER`/`SNOWFLAKE_ROLE` at a
  read-only Snowflake role scoped to `BANKING.ANALYTICS`.
- The LLM is instructed to answer only from retrieved rows, and the UI shows
  the generated SQL and retrieved data for full transparency.
