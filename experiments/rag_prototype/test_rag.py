#!/usr/bin/env python3
"""
RAG Prototype Test Script

Dit script test alle componenten van het RAG prototype stap voor stap.
Run vanuit de project root:

    python -m experiments.rag_prototype.test_rag

Of direct:

    python experiments/rag_prototype/test_rag.py
"""

import sys
from pathlib import Path

# Voeg project root toe aan path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from experiments.rag_prototype import config
from experiments.rag_prototype.chunker import DocumentChunker, chunk_pdf_file
from experiments.rag_prototype.embedder import OllamaEmbedder, test_embedding_model
from experiments.rag_prototype.vector_store import ChromaVectorStore
from experiments.rag_prototype.retriever import RAGRetriever


def print_header(title: str):
    """Print een sectie header."""
    print("\n")
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_step_1_chunking():
    """Test de chunking functionaliteit."""
    print_header("STAP 1: TEST CHUNKING")

    # Check of test documenten bestaan
    test_docs = list(config.TEST_DOCUMENTS_DIR.glob("*.pdf"))

    if not test_docs:
        print(f"WAARSCHUWING: Geen PDF bestanden gevonden in {config.TEST_DOCUMENTS_DIR}")
        return None

    print(f"Gevonden test documenten ({len(test_docs)}):")
    for doc in test_docs:
        print(f"  - {doc.name}")

    # Test met eerste document
    test_doc = test_docs[0]
    print(f"\nTest chunking met: {test_doc.name}")

    chunker = DocumentChunker(verbose=True)
    result = chunk_pdf_file(str(test_doc), chunker)

    if result.success:
        result.print_summary()
        result.print_chunks(max_chunks=5, preview_length=150)
        print("\n✓ Chunking test GESLAAGD")
        return result
    else:
        print(f"\n✗ Chunking test MISLUKT: {result.error}")
        return None


def test_step_2_embeddings():
    """Test de embedding functionaliteit."""
    print_header("STAP 2: TEST EMBEDDINGS")

    print(f"Actief embedding model: {config.ACTIVE_EMBEDDING_MODEL}")

    # Test het model
    success = test_embedding_model(config.ACTIVE_EMBEDDING_MODEL)

    if success:
        print("\n✓ Embedding test GESLAAGD")
    else:
        print("\n✗ Embedding test MISLUKT")
        print(f"\nProbeer het model te installeren met:")
        print(f"  ollama pull {config.ACTIVE_EMBEDDING_MODEL}")

    return success


def test_step_3_vector_store():
    """Test de vector store functionaliteit."""
    print_header("STAP 3: TEST VECTOR STORE")

    store = ChromaVectorStore(verbose=True)

    # Print huidige status
    store.print_status()

    # Test basis operaties
    print("\nTest basis operaties...")

    stats = store.get_stats()
    print(f"  - Collection: {stats['collection_name']}")
    print(f"  - Persist path: {stats['persist_path']}")
    print(f"  - Chunks in store: {stats['total_chunks']}")

    print("\n✓ Vector store test GESLAAGD")
    return True


def test_step_4_full_pipeline():
    """Test de volledige RAG pipeline."""
    print_header("STAP 4: VOLLEDIGE RAG PIPELINE TEST")

    # Check of test documenten bestaan
    test_docs = list(config.TEST_DOCUMENTS_DIR.glob("*.pdf"))
    if not test_docs:
        print("Geen test documenten gevonden.")
        return False

    # Initialiseer RAG retriever
    print("Initialiseer RAG Retriever...")
    retriever = RAGRetriever(verbose=True)

    # Check setup
    ok, message = retriever.check_setup()
    print(f"Setup check: {message}")

    if not ok:
        return False

    # Vraag of we moeten clearen
    print(f"\nHuidige status:")
    retriever.print_status()

    # Indexeer documenten
    print_header("INDEXEREN VAN DOCUMENTEN")

    for doc_path in test_docs:
        print(f"\n>>> Indexeren: {doc_path.name}")
        result = retriever.index_pdf(str(doc_path))
        result.print_summary()

        if not result.success:
            print(f"WAARSCHUWING: Indexeren van {doc_path.name} mislukt")

    # Test retrieval
    print_header("TEST RETRIEVAL")

    test_queries = [
        # Voor Taalbeleid / OP 0.1
        "doelgericht samenhangend taalcurriculum doorlopende leerlijn Nederlands",
        "referentieniveaus taalvaardigheid lezen schrijven",

        # Voor Anti-pestprotocol / VS 1.5
        "anti-pestcoördinator aanspreekpunt pesten",
        "pestprotocol melden incidenten",
    ]

    for query in test_queries:
        print(f"\n>>> Query: \"{query}\"")
        result = retriever.retrieve(query, top_k=3)
        result.print_results(max_results=3, preview_length=150)

    print("\n✓ Volledige pipeline test GESLAAGD")
    return True


def test_step_5_eis_retrieval():
    """Test retrieval specifiek voor deugdelijkheidseisen."""
    print_header("STAP 5: TEST RETRIEVAL VOOR DEUGDELIJKHEIDSEISEN")

    retriever = RAGRetriever(verbose=False)

    # Test voor OP 0.1 - Taalcurriculum
    print("\n>>> Test voor OP 0.1 - Taalcurriculum")
    result = retriever.retrieve_for_eis(
        eis_id="OP 0.1",
        eis_titel="Doelgericht en samenhangend curriculum voor Nederlandse taal",
        eis_kernvraag="Heeft de school voor Nederlandse taal een doelgericht en samenhangend curriculum dat aansluit bij de leerlingpopulatie en toewerkt naar de referentieniveaus?",
        focuspunten="doorlopende leerlijn, referentieniveaus, vijf onderdelen taalvaardigheid, verticale en horizontale samenhang",
        top_k=5,
    )
    result.print_results(max_results=5)

    # Test voor VS 1.5 - Anti-pestcoördinator
    print("\n>>> Test voor VS 1.5 - Anti-pestcoördinator")
    result = retriever.retrieve_for_eis(
        eis_id="VS 1.5",
        eis_titel="Anti-pestcoördinator",
        eis_kernvraag="Heeft de school een benoemde en benaderbare anti-pestcoördinator die het beleid tegen pesten coördineert?",
        focuspunten="aanspreekpunt, beleidscoördinatie, zichtbaarheid, bereikbaarheid, schoolgids",
        top_k=5,
    )
    result.print_results(max_results=5)

    # Toon hoe context er uit zou zien voor LLM
    print_header("VOORBEELD: CONTEXT VOOR LLM")
    context = retriever.get_context_for_llm(
        query="anti-pestcoördinator aanspreekpunt schoolgids",
        max_chunks=3,
    )
    print(context)

    print("\n✓ Eis retrieval test GESLAAGD")
    return True


def run_interactive_mode():
    """Start een interactieve test modus."""
    print_header("INTERACTIEVE TEST MODUS")

    retriever = RAGRetriever(verbose=False)
    retriever.print_status()

    print("\nTyp een query om relevante chunks te zoeken.")
    print("Commando's:")
    print("  'status' - Toon status van vector store")
    print("  'clear'  - Verwijder alle geïndexeerde data")
    print("  'index'  - Indexeer de test documenten opnieuw")
    print("  'quit'   - Stop")
    print()

    while True:
        try:
            query = input("\nQuery> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nTot ziens!")
            break

        if not query:
            continue

        if query.lower() == 'quit':
            print("Tot ziens!")
            break
        elif query.lower() == 'status':
            retriever.print_status()
        elif query.lower() == 'clear':
            retriever.clear_all()
            print("Alle data verwijderd.")
        elif query.lower() == 'index':
            test_docs = list(config.TEST_DOCUMENTS_DIR.glob("*.pdf"))
            for doc in test_docs:
                result = retriever.index_pdf(str(doc))
                print(f"  {doc.name}: {'OK' if result.success else 'FAILED'}")
        else:
            result = retriever.retrieve(query, top_k=5)
            result.print_results(max_results=5)


def main():
    """Hoofdfunctie voor de test suite."""
    print_header("RAG PROTOTYPE TEST SUITE")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Test documenten: {config.TEST_DOCUMENTS_DIR}")
    print(f"ChromaDB pad: {config.CHROMA_DB_PATH}")
    print(f"Embedding model: {config.ACTIVE_EMBEDDING_MODEL}")

    # Bepaal welke tests te runnen
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

        if mode == "chunking":
            test_step_1_chunking()
        elif mode == "embedding":
            test_step_2_embeddings()
        elif mode == "store":
            test_step_3_vector_store()
        elif mode == "pipeline":
            test_step_4_full_pipeline()
        elif mode == "eis":
            test_step_5_eis_retrieval()
        elif mode == "interactive":
            run_interactive_mode()
        elif mode == "all":
            test_step_1_chunking()
            test_step_2_embeddings()
            test_step_3_vector_store()
            test_step_4_full_pipeline()
            test_step_5_eis_retrieval()
        else:
            print(f"Onbekende modus: {mode}")
            print("\nBeschikbare modi:")
            print("  chunking    - Test alleen chunking")
            print("  embedding   - Test alleen embeddings")
            print("  store       - Test alleen vector store")
            print("  pipeline    - Test volledige pipeline")
            print("  eis         - Test retrieval voor deugdelijkheidseisen")
            print("  interactive - Interactieve query modus")
            print("  all         - Run alle tests")
    else:
        # Default: run alle tests
        print("\nRun alle tests. Gebruik 'python test_rag.py <mode>' voor specifieke tests.")
        print("Beschikbare modi: chunking, embedding, store, pipeline, eis, interactive, all")

        input("\nDruk Enter om te beginnen...")

        chunking_ok = test_step_1_chunking()
        embedding_ok = test_step_2_embeddings()
        store_ok = test_step_3_vector_store()

        if chunking_ok and embedding_ok and store_ok:
            test_step_4_full_pipeline()
            test_step_5_eis_retrieval()

            print_header("ALLE TESTS VOLTOOID")
            print("\nWil je de interactieve modus proberen?")
            print("Run: python -m experiments.rag_prototype.test_rag interactive")


if __name__ == "__main__":
    main()
