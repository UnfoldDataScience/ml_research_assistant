import sys
from pathlib import Path

# Add project root to Python path so we can import 'app'
project_root = Path(__file__).resolve().parents[2]  # app/ui/streamlit_app.py -> project root
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd

from app.rag.pipeline import RAGPipeline


def init_pipeline(use_reranking: bool = False, use_evaluation: bool = False) -> RAGPipeline:
    """Initialize pipeline with optional features."""
    key = f"pipeline_rerank_{use_reranking}_eval_{use_evaluation}"
    if key not in st.session_state:
        st.session_state[key] = RAGPipeline(
            use_reranking=use_reranking,
            use_evaluation=use_evaluation,
        )
    return st.session_state[key]


def render_sidebar():
    """Render sidebar with configuration options."""
    st.sidebar.title("🔬 ML Research Assistant")
    st.sidebar.markdown(
        """
        **Workshop: LLM Engineering**
        
        This app demonstrates advanced RAG features:
        - **RAG Evaluation**: 5 metrics to measure retrieval quality
        - **Reranking**: Improve retrieval with cross-encoders
        - **Chunking Strategies**: Different ways to split documents
        
        **Part 2**: Advanced RAG Features
        """
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Settings")
    
    use_reranking = st.sidebar.checkbox(
        "Enable Reranking",
        value=False,  # Disabled by default - requires model download
        help="Use cross-encoder to rerank results for better precision. Note: First use will download a model (~100MB) and may be slow."
    )
    
    use_evaluation = st.sidebar.checkbox(
        "Enable Evaluation",
        value=False,  # Disabled by default for faster responses
        help="Calculate RAG evaluation metrics (Precision, Recall, MRR, NDCG, F1)"
    )
    
    top_k = st.sidebar.slider(
        "Number of chunks (top_k)",
        min_value=3,
        max_value=10,
        value=5,
        help="How many chunks to retrieve and use"
    )
    
    return use_reranking, use_evaluation, top_k


def render_evaluation_metrics(metrics: dict):
    """Render evaluation metrics in a nice format."""
    st.subheader("📊 RAG Evaluation Metrics")
    st.markdown(
        """
        These metrics help us understand how well our retrieval system is performing:
        - **Precision@K**: Fraction of retrieved items that are relevant
        - **Recall@K**: Fraction of relevant items that were retrieved
        - **MRR**: Mean Reciprocal Rank (quality of first relevant result)
        - **NDCG@K**: Normalized Discounted Cumulative Gain (ranking quality)
        - **F1@K**: Harmonic mean of Precision and Recall
        """
    )
    
    # Create metrics display
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Precision@K", f"{metrics.get('precision@k', 0):.3f}")
    with col2:
        st.metric("Recall@K", f"{metrics.get('recall@k', 0):.3f}")
    with col3:
        st.metric("MRR", f"{metrics.get('mrr', 0):.3f}")
    with col4:
        st.metric("NDCG@K", f"{metrics.get('ndcg@k', 0):.3f}")
    with col5:
        st.metric("F1@K", f"{metrics.get('f1@k', 0):.3f}")
    
    # Show explanation
    with st.expander("📖 Understanding the Metrics"):
        st.markdown("""
        **Precision@K**: Measures how many of the top-K results are actually relevant.
        - High precision = fewer irrelevant results
        
        **Recall@K**: Measures how many relevant items we found in top-K.
        - High recall = we're not missing relevant content
        
        **MRR**: Measures where the first relevant result appears.
        - Higher MRR = relevant results appear earlier
        
        **NDCG@K**: Measures ranking quality with position discounting.
        - Higher NDCG = better ordering of results
        
        **F1@K**: Balanced measure combining precision and recall.
        - Good overall performance indicator
        """)


def render_reranking_comparison(comparison: dict):
    """Render reranking comparison visualization."""
    st.subheader("🔄 Reranking Comparison")
    st.markdown(
        """
        **Reranking** uses a cross-encoder model to reorder results by considering
        the query and document together. This typically improves precision of top results.
        
        **Why it helps:**
        - Initial retrieval uses bi-encoder (fast, independent embeddings)
        - Reranking uses cross-encoder (slower, but sees query+document together)
        - Cross-encoders capture complex semantic relationships better
        """
    )
    
    original = comparison.get("original", [])
    reranked = comparison.get("reranked", [])
    position_changes = comparison.get("position_changes", 0)
    avg_score = comparison.get("avg_rerank_score", 0.0)
    if avg_score is None:
        avg_score = 0.0
    
    # Show statistics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Position Changes", position_changes)
    with col2:
        st.metric("Avg Rerank Score", f"{avg_score:.3f}")
    
    # Show comparison table
    if original and reranked:
        st.markdown("#### Before vs After Reranking")
        
        comparison_data = []
        for i, (orig, rerank) in enumerate(zip(original[:5], reranked[:5]), 1):
            # Safely handle None values - .get() returns None if key exists with None value
            orig_score_val = orig.get('score')
            orig_score = float(orig_score_val) if orig_score_val is not None else 0.0
            
            rerank_score_val = rerank.get('rerank_score')
            rerank_score = float(rerank_score_val) if rerank_score_val is not None else 0.0
            
            comparison_data.append({
                "Rank": i,
                "Original Title": (orig.get("title") or "")[:50] + "...",
                "Original Score": f"{orig_score:.4f}",
                "Reranked Title": (rerank.get("title") or "")[:50] + "...",
                "Rerank Score": f"{rerank_score:.3f}",
                "Moved": "✅" if id(orig) != id(rerank) else "➡️"
            })
        
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Show explanation
        with st.expander("💡 How Reranking Works"):
            st.markdown("""
            1. **Initial Retrieval**: Bi-encoder finds ~10-20 candidate chunks quickly
            2. **Reranking**: Cross-encoder scores each query-chunk pair more accurately
            3. **Reordering**: Results are sorted by rerank scores
            4. **Result**: Top-K most relevant chunks for the query
            
            **Trade-off**: Reranking is slower but more accurate, so we only apply it
            to a small set of candidates (not the entire database).
            """)


def render_chunking_info(contexts: list):
    """Show chunking strategy information."""
    st.subheader("✂️ Chunking Strategy Information")
    st.markdown(
        """
        Different chunking strategies affect how documents are split and stored.
        This impacts retrieval quality and context preservation.
        """
    )
    
    # Analyze chunks to show strategy
    strategies = {}
    for ctx in contexts:
        strategy = ctx.get("chunking_strategy", "fixed_size")
        strategies[strategy] = strategies.get(strategy, 0) + 1
    
    if strategies:
        st.markdown("#### Current Chunks by Strategy")
        strategy_df = pd.DataFrame([
            {"Strategy": k, "Count": v}
            for k, v in strategies.items()
        ])
        st.dataframe(strategy_df, use_container_width=True, hide_index=True)
    
    # Show chunking strategies comparison
    with st.expander("📚 Chunking Strategies Explained"):
        st.markdown("""
        **1. Fixed-Size Chunking** (Current default)
        - Splits text into fixed token windows
        - Pros: Simple, consistent sizes
        - Cons: May break sentences/context
        
        **2. Sentence-Based Chunking**
        - Splits at sentence boundaries
        - Pros: Preserves sentence integrity
        - Cons: Variable chunk sizes
        
        **3. Semantic Chunking**
        - Groups semantically similar content
        - Pros: Keeps related content together
        - Cons: More complex, requires embeddings
        
        **Impact on RAG:**
        - Better chunking = better context preservation
        - Better context = more accurate retrieval
        - Semantic chunking often performs best for complex queries
        """)


def main():
    st.set_page_config(
        page_title="ML Research Assistant - Advanced RAG",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    use_reranking, use_evaluation, top_k = render_sidebar()
    pipeline = init_pipeline(use_reranking, use_evaluation)

    st.title("🔍 ML Research Assistant")
    st.markdown(
        """
        Ask a question about machine learning / deep learning. 
        The assistant will search arXiv-style papers and answer using retrieved context.
        
        **Educational Features**: This app demonstrates RAG evaluation, reranking, and chunking strategies.
        """
    )

    query = st.text_input(
        "Your question:",
        value="What is variational inference?",
        help="Enter your question about ML/DL research"
    )
    
    # Simple search button below the text box - centered and properly sized
    st.markdown("""
    <style>
    /* Style search button to be simple, properly sized, and readable */
    .stButton > button {
        width: 160px !important;
        min-height: 36px !important;
        height: auto !important;
        padding: 0.4rem 1.2rem !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Center the button below the text input
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        search_clicked = st.button("🔍 Search", type="primary", use_container_width=False, key="search_btn")
    
    if search_clicked:
        if not query.strip():
            st.warning("Please enter a question.")
        else:
            # Show appropriate spinner message
            spinner_msg = "🔍 Retrieving and generating answer..."
            if use_reranking:
                spinner_msg = "🔍 Retrieving, reranking, and generating answer... (reranking may take 30-60s on first use)"
            elif use_evaluation:
                spinner_msg = "🔍 Retrieving, evaluating, and generating answer..."
            
            with st.spinner(spinner_msg):
                try:
                    result = pipeline.answer_query(
                        query,
                        top_k=top_k,
                        use_reranking=use_reranking,
                        use_evaluation=use_evaluation,
                    )
                    st.session_state["last_result"] = result
                except RuntimeError as e:
                    if "reranker" in str(e).lower() or "rerank" in str(e).lower():
                        st.error(f"⚠️ Reranking failed: {str(e)}\n\n**Tip:** Try disabling reranking in the sidebar settings for faster responses.")
                        # Fall back to non-reranked result
                        try:
                            result = pipeline.answer_query(
                                query,
                                top_k=top_k,
                                use_reranking=False,
                                use_evaluation=use_evaluation,
                            )
                            st.session_state["last_result"] = result
                            st.info("✅ Showing results without reranking.")
                        except Exception as e2:
                            st.error(f"Error: {e2}")
                    else:
                        st.error(f"Error: {e}")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

    result = st.session_state.get("last_result")
    if not result:
        st.info("👆 Enter a question and click 'Search & Answer' to see results.")
        return

    # Main content area
    st.divider()
    
    # Answer section
    st.subheader("💬 Answer")
    st.markdown(result.answer)
    st.caption("Model-generated answer from retrieved context chunks.")

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Evaluation Metrics",
        "🔄 Reranking",
        "✂️ Chunking Info",
        "📄 Retrieved Chunks"
    ])

    with tab1:
        if result.evaluation_metrics:
            render_evaluation_metrics(result.evaluation_metrics)
        else:
            st.info("Enable 'Evaluation' in sidebar to see metrics.")

    with tab2:
        if result.reranking_comparison:
            render_reranking_comparison(result.reranking_comparison)
        else:
            st.info("Enable 'Reranking' in sidebar to see comparison.")

    with tab3:
        render_chunking_info(result.contexts)

    with tab4:
        st.subheader("📄 Retrieved Chunks")
        st.markdown(
            "These are the chunks retrieved from the vector database. "
            "Each chunk contains relevant context from research papers."
        )
        
        for i, ctx in enumerate(result.contexts, start=1):
            with st.expander(f"Chunk {i} · {ctx.get('title', 'Unknown')[:60]}..."):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Paper ID:** {ctx.get('paper_id', 'N/A')}")
                    st.markdown(f"**Title:** {ctx.get('title', 'N/A')}")
                with col2:
                    st.markdown(f"**Token range:** {ctx.get('start_token', 0)} – {ctx.get('end_token', 0)}")
                    score = ctx.get("score")
                    if score is not None:
                        st.markdown(f"**Similarity Score:** {score:.4f}")
                    rerank_score = ctx.get("rerank_score")
                    if rerank_score is not None:
                        st.markdown(f"**Rerank Score:** {rerank_score:.3f}")
                    chunking_strategy = ctx.get("chunking_strategy")
                    if chunking_strategy:
                        st.markdown(f"**Strategy:** {chunking_strategy}")
                
                st.divider()
                st.markdown("**Chunk Text:**")
                st.markdown(ctx.get("chunk_text", ""))


if __name__ == "__main__":
    main()
