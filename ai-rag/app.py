"""
AI Banking Data Assistant — Streamlit UI

A lightweight chatbot on top of the existing Snowflake Gold layer
(BANKING.ANALYTICS: dim_customers, dim_accounts, fact_transactions).

Run with:
    streamlit run app.py
"""

import pandas as pd
import streamlit as st
from rag.config import Config
from rag.pipeline import answer_question

st.set_page_config(page_title="BankPulse AI", page_icon="🏦", layout="centered")

st.title("🏦 BankPulse AI")
st.caption(
    "Ask questions about customers, accounts, and transactions. "
    "Answers are generated from the Snowflake **Gold layer** — not invented."
)

missing = Config.validate()
if missing:
    st.error(
        "Missing configuration: " + ", ".join(missing) +
        ".\n\nCopy `.env.example` to `.env` and fill in the values."
    )
    st.stop()

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.markdown("### About")
    st.markdown(
        "This assistant sits **on top of** the existing data pipeline:\n\n"
        "`Postgres → Kafka/Debezium → MinIO → Airflow → Snowflake "
        "(Bronze → Silver → Gold) → dbt`\n\n"
        "It never modifies the pipeline or the Gold data — it only reads it."
    )
    st.markdown("### Example questions")
    st.markdown(
        "- How many customers are there?\n"
        "- What is the total transaction volume?\n"
        "- Which customers have the highest transaction activity?\n"
        "- What is the total balance across all accounts?\n"
        "- Which accounts had the most transactions?\n"
        "- Give me a summary of banking activity.\n"
    )
    if st.button("Clear conversation"):
        st.session_state.history = []
        st.rerun()

# Render past turns
for turn in st.session_state.history:
    with st.chat_message("user"):
        st.write(turn["question"])
    with st.chat_message("assistant"):
        st.write(turn["result"].answer)
        if turn["result"].sql:
            with st.expander("🔍 Show how this was answered"):
                st.markdown(f"**Source table(s):** {', '.join(turn['result'].source_tables) or '—'}")
                st.markdown("**Generated SQL:**")
                st.code(turn["result"].sql, language="sql")
                if turn["result"].rows:
                    st.markdown("**Retrieved data:**")
                    df = pd.DataFrame(turn["result"].rows, columns=turn["result"].columns)
                    st.dataframe(df, use_container_width=True)
        if turn["result"].error:
            st.caption(f"⚠️ {turn['result'].error}")

question = st.chat_input("Ask a question about the banking data...")

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving data from the Gold layer and generating an answer..."):
            result = answer_question(question)
        st.write(result.answer)
        if result.sql:
            with st.expander("🔍 Show how this was answered"):
                st.markdown(f"**Source table(s):** {', '.join(result.source_tables) or '—'}")
                st.markdown("**Generated SQL:**")
                st.code(result.sql, language="sql")
                if result.rows:
                    st.markdown("**Retrieved data:**")
                    df = pd.DataFrame(result.rows, columns=result.columns)
                    st.dataframe(df, use_container_width=True)
        if result.error:
            st.caption(f"⚠️ {result.error}")

    st.session_state.history.append({"question": question, "result": result})
