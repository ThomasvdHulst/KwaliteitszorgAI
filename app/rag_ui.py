"""
RAG UI componenten voor de Streamlit applicatie.

Dit bestand bevat de UI voor:
- Document databank beheer (upload, lijst, verwijderen)
- RAG toggle voor het gebruik van de databank
- Status weergave van de RAG retriever
"""

import streamlit as st
from typing import Optional, Tuple, List

from config import settings
from src.kwaliteitszorg.rag import config as rag_config


def get_rag_retriever():
    """
    Haal de RAG retriever uit session state of maak nieuwe aan.

    Returns:
        RAGRetriever instance of None als niet beschikbaar
    """
    if "rag_retriever" not in st.session_state:
        try:
            from src.kwaliteitszorg.rag import RAGRetriever
            st.session_state.rag_retriever = RAGRetriever(verbose=False)

            # Check setup
            ok, message = st.session_state.rag_retriever.check_setup()
            if not ok:
                st.session_state.rag_setup_error = message
                return None

            st.session_state.rag_setup_error = None
        except Exception as e:
            st.session_state.rag_setup_error = str(e)
            return None

    return st.session_state.rag_retriever


def init_rag_state():
    """Initialiseer RAG session state variabelen."""
    if "rag_enabled" not in st.session_state:
        st.session_state.rag_enabled = False
    if "rag_context" not in st.session_state:
        st.session_state.rag_context = None
    if "rag_selected_docs" not in st.session_state:
        st.session_state.rag_selected_docs = None  # None = alles geselecteerd
    if "rag_used_sources" not in st.session_state:
        st.session_state.rag_used_sources = []  # Lijst van gebruikte documenten


def render_document_databank():
    """
    Render de document databank beheer sectie.

    Toont:
    - Upload functie voor nieuwe documenten
    - Lijst van geïndexeerde documenten
    - Verwijder knoppen per document
    """
    st.markdown("### Document Databank")

    retriever = get_rag_retriever()

    if retriever is None:
        error = st.session_state.get("rag_setup_error", "Onbekende fout")
        st.error(f"RAG niet beschikbaar: {error}")
        st.info("Zorg dat het embedding model is geïnstalleerd: `ollama pull nomic-embed-text-v2-moe`")
        return

    # Toon huidige documenten
    documents = retriever.list_indexed_documents()

    if documents:
        st.markdown(f"**{len(documents)} document(en) geïndexeerd:**")

        for doc in documents:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.text(f"📄 {doc['document_name']}")
            with col2:
                st.caption(f"{doc['chunk_count']} chunks")
            with col3:
                if st.button("🗑️", key=f"delete_{doc['document_id']}", help="Verwijder document"):
                    retriever.delete_document(doc['document_id'])
                    st.rerun()
    else:
        st.info("Nog geen documenten geïndexeerd. Upload documenten om te beginnen.")

    # Upload sectie
    st.markdown("---")
    st.markdown("**Nieuw document toevoegen:**")

    uploaded_file = st.file_uploader(
        "Kies een PDF",
        type=["pdf"],
        key="rag_document_upload",
        help="Upload een beleidsdocument om toe te voegen aan de databank",
    )

    if uploaded_file is not None:
        if st.button("Indexeer document", type="primary"):
            with st.spinner(f"Document indexeren... Dit kan even duren."):
                # Extract text from PDF - unlimited voor RAG
                from src.kwaliteitszorg.utils.pdf_processor import extract_text_from_pdf

                result = extract_text_from_pdf(
                    file_bytes=uploaded_file.read(),
                    filename=uploaded_file.name,
                    unlimited=True,  # Geen limieten voor RAG indexering
                )

                if not result.success:
                    st.error(f"PDF extractie mislukt: {result.error}")
                    return

                # Index the text with page boundaries
                index_result = retriever.index_text(
                    text=result.text,
                    document_name=uploaded_file.name,
                    page_boundaries=result.page_boundaries,
                )

                if index_result.success:
                    st.success(f"Document geïndexeerd: {index_result.chunks_indexed} chunks ({result.char_count:,} karakters, {result.page_count} pagina's)")
                    st.rerun()
                else:
                    st.error(f"Indexeren mislukt: {index_result.error}")
                    # Toon extra info voor debugging
                    with st.expander("Details"):
                        st.write(f"Pagina's verwerkt: {result.page_count}")
                        st.write(f"Karakters: {result.char_count:,}")
                        st.write(f"Chunks gemaakt: {index_result.chunks_created}")


def render_rag_toggle(eis_id: str, eis: dict) -> Tuple[bool, Optional[str], List[str]]:
    """
    Render de RAG toggle met document selectie en haal context op.

    Args:
        eis_id: ID van de geselecteerde eis
        eis: Dict met eis informatie (moet retrieval_query bevatten)

    Returns:
        Tuple van (rag_enabled, rag_context, used_sources)
    """
    init_rag_state()

    retriever = get_rag_retriever()

    if retriever is None or retriever.is_empty():
        # RAG niet beschikbaar of geen documenten
        return False, None, []

    # Toggle voor RAG
    st.markdown("### Documentdatabank (RAG)")

    documents = retriever.list_indexed_documents()

    rag_enabled = st.toggle(
        "Gebruik documentdatabank",
        value=st.session_state.rag_enabled,
        key="rag_toggle",
        help="Schakel in om automatisch relevante passages uit je documentdatabank te gebruiken",
    )

    st.session_state.rag_enabled = rag_enabled

    if not rag_enabled:
        st.session_state.rag_context = None
        st.session_state.rag_used_sources = []
        return False, None, []

    # === DOCUMENT SELECTIE ===
    st.markdown("**Selecteer documenten:**")

    # Initialiseer selectie als nog niet gedaan
    if st.session_state.rag_selected_docs is None:
        st.session_state.rag_selected_docs = [d['document_id'] for d in documents]

    # Select all / Deselect all knoppen
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Alles", key="rag_select_all", help="Selecteer alle documenten"):
            st.session_state.rag_selected_docs = [d['document_id'] for d in documents]
            st.rerun()
    with col2:
        if st.button("Geen", key="rag_select_none", help="Deselecteer alle documenten"):
            st.session_state.rag_selected_docs = []
            st.rerun()

    # Checkboxes voor elk document
    selected_doc_ids = []
    for doc in documents:
        is_selected = doc['document_id'] in st.session_state.rag_selected_docs
        if st.checkbox(
            f"📄 {doc['document_name']} ({doc['chunk_count']} chunks)",
            value=is_selected,
            key=f"rag_doc_{doc['document_id']}",
        ):
            selected_doc_ids.append(doc['document_id'])

    # Update session state
    st.session_state.rag_selected_docs = selected_doc_ids

    # Als geen documenten geselecteerd, geen RAG context
    if not selected_doc_ids:
        st.session_state.rag_context = None
        st.session_state.rag_used_sources = []
        return True, None, []

    st.markdown("---")

    # === RETRIEVAL ===
    retrieval_query = eis.get("retrieval_query", "")

    if not retrieval_query:
        st.warning("Deze eis heeft geen geoptimaliseerde zoekquery. RAG werkt mogelijk minder goed.")
        retrieval_query = eis.get("titel", eis_id)

    # Retrieve relevante chunks alleen uit geselecteerde documenten
    result = retriever.retrieve_for_eis(
        retrieval_query,
        top_k=rag_config.DEFAULT_TOP_K,
        filter_document_ids=selected_doc_ids,
    )

    if not result.success:
        st.error(f"Fout bij ophalen passages: {result.error}")
        return False, None, []

    if not result.chunks:
        st.info("Geen relevante passages gevonden in de geselecteerde documenten.")
        st.session_state.rag_used_sources = []
        return True, None, []

    # Haal gebruikte bronnen op
    used_sources = result.get_used_documents()
    st.session_state.rag_used_sources = used_sources

    # Format context voor LLM
    rag_context = result.format_context_for_llm(max_chunks=rag_config.DEFAULT_TOP_K)

    # Toon preview van gevonden passages
    with st.expander(f"Gevonden passages ({len(result.chunks)})", expanded=False):
        for i, chunk in enumerate(result.chunks[:3], 1):
            st.markdown(f"**Passage {i}** ({chunk.similarity_score:.0%} match)")
            st.caption(f"Bron: {chunk.document_name}")
            st.text(chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text)
            st.markdown("---")

        if len(result.chunks) > 3:
            st.caption(f"... en {len(result.chunks) - 3} meer")

    # Note: used_sources wordt teruggegeven zodat de caller kan tracken
    # welke bronnen de AI daadwerkelijk gebruikt in het antwoord
    st.session_state.rag_context = rag_context
    return True, rag_context, used_sources


def render_databank_management_page():
    """
    Render een volledige pagina voor databank beheer.

    Dit kan als aparte pagina of in een expander worden gebruikt.
    """
    st.markdown("## Document Databank Beheer")

    st.markdown("""
    Met de document databank kun je meerdere beleidsdocumenten indexeren.
    De AI gebruikt dan automatisch relevante passages uit al je documenten
    om je te helpen bij het invullen van deugdelijkheidseisen.
    """)

    render_document_databank()

    # Toon statistieken
    retriever = get_rag_retriever()
    if retriever:
        stats = retriever.get_stats()
        st.markdown("---")
        st.markdown("**Statistieken:**")
        st.caption(f"Totaal chunks: {stats['total_chunks']}")
        st.caption(f"Embedding dimensies: {stats['embedding_dimensions']}")

        # Clear all button
        if stats['total_chunks'] > 0:
            st.markdown("---")
            if st.button("Wis alle documenten", type="secondary"):
                retriever.clear_all()
                st.success("Alle documenten verwijderd")
                st.rerun()
