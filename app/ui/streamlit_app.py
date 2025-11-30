import streamlit as st

from app.rag.pipeline import RAGPipeline


def init_pipeline() -> RAGPipeline:
    if "pipeline" not in st.session_state:
        st.session_state["pipeline"] = RAGPipeline()
    return st.session_state["pipeline"]


def render_sidebar():
    st.sidebar.title("ML Research Assistant")
    st.sidebar.markdown(
        """
        **Version:** v1 (Baseline RAG)

        This app searches over ML research papers (arXiv subset)
        and answers your questions using a retrieval-augmented LLM.

        - Session 1: Baseline RAG (this)
        """
    )


def main():
    st.set_page_config(
        page_title="ML Research Assistant",
        layout="wide",
    )

    render_sidebar()
    pipeline = init_pipeline()

    st.title("🔍 ML Research Assistant")
    st.write(
        "Ask a question about machine learning / deep learning. "
        "The assistant will search arXiv-style papers and answer using retrieved context."
    )

    query = st.text_input("Your question:", value="What is variational inference?")

    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button("Search & Answer", type="primary"):
            if not query.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Thinking..."):
                    result = pipeline.answer_query(query, top_k=5)
                    st.session_state["last_result"] = result

        result = st.session_state.get("last_result")
        if result:
            st.subheader("Answer")
            st.write(result.answer)
            st.caption("Model-generated answer from retrieved context.")

    with col2:
        st.subheader("Retrieved Chunks")
        st.write(
            "These are the chunks fetched from the vector database. "
            "In Session 2, we'll improve this retrieval a lot."
        )

        result = st.session_state.get("last_result")
        if result:
            for i, ctx in enumerate(result.contexts, start=1):
                with st.expander(f"Chunk {i} · {ctx['title'][:60]}..."):
                    st.markdown(f"**Paper ID:** {ctx['paper_id']}")
                    st.markdown(
                        f"**Token range:** {ctx['start_token']} – {ctx['end_token']}"
                    )
                    score = ctx.get("score")
                    if score is not None:
                        st.markdown(f"**Score (distance):** {score:.4f}")
                    st.markdown("---")
                    st.markdown(ctx["chunk_text"])
        else:
            st.info("Run a query to see retrieved chunks here.")


if __name__ == "__main__":
    main()
