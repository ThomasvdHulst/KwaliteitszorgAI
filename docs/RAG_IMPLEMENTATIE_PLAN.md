# RAG Implementatie Plan - Kwaliteitszorg AI

## 1. Wat is RAG en waarom past het bij onze use case?

### Het probleem
Scholen hebben meerdere beleidsdocumenten (taalbeleid, veiligheidsplan, schoolplan, etc.) die relevant kunnen zijn voor verschillende deugdelijkheidseisen. De huidige aanpak (heel document in context) heeft beperkingen:
- Context window limiet (~32K tokens voor Gemma3)
- Meerdere documenten passen niet in één prompt
- Irrelevante delen verdunnen de relevante informatie

### De oplossing: RAG (Retrieval Augmented Generation)
RAG werkt in drie stappen:
1. **Indexeren**: Documenten worden opgesplitst in chunks en omgezet naar embeddings (numerieke vectoren die de betekenis vastleggen)
2. **Retrieval**: Bij een vraag worden de meest relevante chunks opgehaald via similarity search
3. **Generatie**: Alleen de relevante chunks worden meegegeven aan het LLM

### Waarom past dit bij Kwaliteitszorg AI?
- School kan **meerdere documenten** koppelen aan hun databank
- Per **deugdelijkheidseis** worden automatisch de **relevante passages** opgehaald
- AI kan **specifiek citeren** uit de juiste documenten
- Schaalt naar **grote hoeveelheden** documenten
- Blijft **volledig lokaal** (privacy-first)

---

## 2. Voorgestelde Architectuur

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SCHOOL DOCUMENT DATABANK                      │
│  [Taalbeleid.pdf] [Veiligheidsplan.pdf] [Schoolplan.pdf] [...]      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DOCUMENT PROCESSOR                           │
│  1. PDF → Tekst extractie (PyMuPDF - bestaande code)                │
│  2. Chunking (semantic/paragraph-based, ~300-500 tokens)            │
│  3. Metadata toevoegen (document_name, page, section, chunk_id)     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         EMBEDDING GENERATOR                          │
│  Ollama + nomic-embed-text (768 dimensies, lokaal)                  │
│  - Chunk tekst → Vector embedding                                   │
│  - Eis omschrijving → Vector embedding (voor retrieval)             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         VECTOR DATABASE                              │
│  ChromaDB (lokaal, persistent, geen externe dependencies)           │
│  Opslag: embedding + metadata per chunk                             │
│  Collections per school (of globale collectie met school_id)        │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         RETRIEVAL ENGINE                             │
│  Query: Eis omschrijving + focuspunten + gebruikersvraag            │
│  → Similarity search in ChromaDB                                    │
│  → Top-K relevante chunks ophalen (K=5-10)                          │
│  → Optioneel: reranking voor betere precisie                        │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         CONTEXT BUILDER                              │
│  Relevante chunks formatteren met metadata:                         │
│  [Bron: Taalbeleid.pdf, p.3]                                        │
│  "De school hanteert een doorlopende leerlijn..."                   │
│  → Wordt toegevoegd aan system prompt                               │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         LLM GENERATION                               │
│  Ollama + Gemma3:27b (bestaande setup)                              │
│  System prompt + relevante chunks + eis info + vraag                │
│  → Antwoord met bronverwijzingen                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technische Keuzes

### Embedding Model: `nomic-embed-text` via Ollama
**Waarom:**
- Lokaal, geen API kosten
- Integreert naadloos met bestaande Ollama setup
- 768 dimensies, goede performance
- Ondersteunt lange context (8192 tokens)
- Presteert beter dan OpenAI text-embedding-ada-002

**Installatie:**
```bash
ollama pull nomic-embed-text
```

### Vector Database: ChromaDB
**Waarom:**
- Open-source, volledig lokaal
- Geen externe dependencies of servers nodig
- Persistent storage (data blijft behouden)
- Eenvoudige Python API
- Native Ollama integratie
- Beginner-friendly maar production-ready

**Installatie:**
```bash
pip install chromadb
```

### Chunking Strategie: Semantic/Paragraph-based
**Waarom:**
- Beter dan fixed-size voor beleidsdocumenten
- Behoudt context en betekenis
- Respecteert natuurlijke grenzen (paragrafen, secties)

**Parameters:**
- Target chunk size: 300-500 tokens (~200-350 woorden)
- Overlap: 10-15% (50-75 tokens)
- Respecteer paragraph boundaries
- Behoud sectie-headers in chunks

---

## 4. Metadata Structuur per Chunk

```python
{
    "chunk_id": "uuid-string",
    "document_id": "uuid-string",
    "document_name": "Taalbeleid 2024.pdf",
    "document_type": "beleidsdocument",  # optioneel: taalbeleid, veiligheidsplan, etc.
    "page_number": 3,
    "section_header": "3.2 Doorlopende leerlijn",  # indien beschikbaar
    "chunk_index": 5,  # positie in document
    "total_chunks": 23,  # totaal chunks in document
    "char_start": 4521,  # positie in originele tekst
    "char_end": 5102,
    "school_id": "school-uuid",  # voor multi-tenant setup
    "created_at": "2025-01-30T10:00:00Z",
    "embedding_model": "nomic-embed-text"
}
```

---

## 5. Retrieval Strategie

### Query Constructie
Voor optimale retrieval combineren we:
1. **Eis-specifieke query**: De kernvraag + focuspunten van de deugdelijkheidseis
2. **PDCA-specifieke query**: Afhankelijk van welk veld (ambitie, acties, etc.)
3. **Gebruikersvraag**: Indien aanvullende context

Voorbeeld query voor OP 0.1 (Taalcurriculum):
```
"doelgericht samenhangend taalcurriculum doorlopende leerlijn
referentieniveaus taalvaardigheid Nederlands kerndoelen"
```

### Retrieval Parameters
- **Top-K**: Start met K=10, tune op basis van resultaten
- **Similarity threshold**: Minimaal 0.7 cosine similarity
- **Diversiteit**: Prefereer chunks uit verschillende documenten

### Optioneel: Reranking
Voor betere precisie kan een reranker de top-K results herordenen:
- Simpel: Ollama met korte prompt "Is dit relevant voor [eis]?"
- Geavanceerd: Cross-encoder model

---

## 6. Stapsgewijs Implementatieplan

### Fase 1: Prototype/Sandbox (Week 1) ⬅️ EERSTE SESSIE
**Doel:** Proof of concept in geïsoleerde omgeving

```
experiments/
└── rag_prototype/
    ├── __init__.py
    ├── chunker.py          # Document chunking logica
    ├── embedder.py         # Ollama embedding wrapper
    ├── vector_store.py     # ChromaDB wrapper
    ├── retriever.py        # Retrieval logica
    ├── test_rag.py         # Test script
    ├── data/
    │   └── test_documents/ # Test PDFs
    └── chroma_db/          # Persistent ChromaDB storage
```

**Deliverables:**
- [ ] Werkende chunker met metadata
- [ ] Embedding generatie via Ollama
- [ ] ChromaDB opslag en retrieval
- [ ] Test met 2-3 voorbeelddocumenten
- [ ] Evaluatie: zijn de opgehaalde chunks relevant?

### Fase 2: Integratie Voorbereiding (Week 2)
**Doel:** RAG module production-ready maken

- [ ] Error handling en logging
- [ ] Configuratie via settings.py
- [ ] Document management (toevoegen, verwijderen, updaten)
- [ ] Batch processing voor meerdere documenten
- [ ] Performance optimalisatie

### Fase 3: UI Integratie (Week 3)
**Doel:** RAG koppelen aan Streamlit interface

- [ ] Document upload naar RAG databank
- [ ] Document selectie per eis
- [ ] "Genereer invulling vanuit documenten" functie
- [ ] Bronverwijzingen in AI responses
- [ ] Progress indicators tijdens indexering

### Fase 4: Evaluatie & Tuning (Week 4)
**Doel:** Optimaliseren op basis van echte gebruik

- [ ] Chunk size tuning
- [ ] Retrieval threshold tuning
- [ ] Query constructie verfijnen
- [ ] A/B testing met verschillende strategieën
- [ ] Feedback loop met gebruikers

---

## 7. Eerste Sessie: Wat gaan we bouwen?

### Scope
Een standalone prototype in `experiments/rag_prototype/` dat:
1. Een PDF document inleest en chunked
2. Chunks embed met Ollama nomic-embed-text
3. Chunks opslaat in ChromaDB met metadata
4. Een query kan uitvoeren en relevante chunks teruggeeft
5. De kwaliteit van retrieval test

### Benodigde Dependencies
```
chromadb>=0.4.0
```
(PyMuPDF en ollama zijn al geïnstalleerd)

### Test Scenario
We gebruiken een van de voorbeelddocumenten uit `voorbeeldbeleid/` (als die er zijn) of maken een test document. We testen retrieval voor OP 0.1 (Taalcurriculum) of VS 1.5 (Anti-pestcoördinator).

### Success Criteria
- [ ] Chunks bevatten juiste metadata (document naam, pagina)
- [ ] Embeddings worden correct gegenereerd
- [ ] ChromaDB persisteert data na restart
- [ ] Query voor "doorlopende leerlijn taal" haalt relevante chunks op
- [ ] Irrelevante chunks scoren lager

---

## 8. Code Structuur Prototype

```python
# experiments/rag_prototype/chunker.py
class DocumentChunker:
    def chunk_document(self, text: str, metadata: dict) -> List[Chunk]
    def chunk_by_paragraphs(self, text: str) -> List[str]
    def add_overlap(self, chunks: List[str], overlap: int) -> List[str]

# experiments/rag_prototype/embedder.py
class OllamaEmbedder:
    def embed_text(self, text: str) -> List[float]
    def embed_batch(self, texts: List[str]) -> List[List[float]]

# experiments/rag_prototype/vector_store.py
class ChromaVectorStore:
    def __init__(self, persist_path: str)
    def add_chunks(self, chunks: List[Chunk], embeddings: List[List[float]])
    def query(self, query_text: str, top_k: int = 10) -> List[RetrievedChunk]
    def delete_document(self, document_id: str)

# experiments/rag_prototype/retriever.py
class RAGRetriever:
    def __init__(self, embedder, vector_store)
    def index_document(self, file_path: str) -> IndexResult
    def retrieve_for_eis(self, eis_id: str, top_k: int = 10) -> List[RetrievedChunk]
    def format_context(self, chunks: List[RetrievedChunk]) -> str
```

---

## 9. Risico's en Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Chunks te klein/groot | Slechte retrieval | Experimenteer met sizes in prototype |
| Embeddings te traag | Slechte UX | Batch processing, progress indicator |
| Irrelevante chunks | AI haalt verkeerde info | Query tuning, reranking |
| ChromaDB schaalt niet | Performance issues | Monitoring, eventueel FAISS als alternatief |
| Privacy concerns | Gevoelige data | Alles lokaal, geen cloud |

---

## 10. Bronnen

### RAG Best Practices
- [Weaviate: Chunking Strategies](https://weaviate.io/blog/chunking-strategies-for-rag)
- [Stack Overflow: Practical Tips for RAG](https://stackoverflow.blog/2024/08/15/practical-tips-for-retrieval-augmented-generation-rag/)
- [2025 Guide to RAG](https://www.edenai.co/post/the-2025-guide-to-retrieval-augmented-generation-rag)

### Ollama Embeddings
- [Ollama: nomic-embed-text](https://ollama.com/library/nomic-embed-text)
- [Ollama Blog: Embedding Models](https://ollama.com/blog/embedding-models)
- [Medium: RAG with Ollama](https://medium.com/@rahul.dusad/run-rag-pipeline-locally-with-ollama-embedding-model-nomic-embed-text-generate-model-llama3-e7a554a541b3)

### ChromaDB
- [Real Python: ChromaDB Tutorial](https://realpython.com/chromadb-vector-database/)
- [ChromaDB + Ollama Cookbook](https://cookbook.chromadb.dev/integrations/ollama/embeddings/)
- [Medium: RAG with ChromaDB & Ollama](https://medium.com/@arunpatidar26/rag-chromadb-ollama-python-guide-for-beginners-30857499d0a0)

### Metadata & Source Tracking
- [Metadata-Aware Chunking](https://medium.com/@asimsultan2/metadata-aware-chunking-the-secret-to-production-ready-rag-pipelines-85bc25b12350)
- [Airbyte: Document Chunking Best Practices](https://airbyte.com/agentic-data/ag-document-chunking-best-practices)

---

## Volgende Stap

**Klaar om te beginnen?**

De eerste sessie focust op het bouwen van het prototype in `experiments/rag_prototype/`. We beginnen met:
1. Directory structuur opzetten
2. `chunker.py` implementeren
3. `embedder.py` implementeren met Ollama
4. `vector_store.py` implementeren met ChromaDB
5. Test met een voorbeelddocument

Dit geeft ons een werkend proof-of-concept waarmee we de kwaliteit van chunking en retrieval kunnen evalueren voordat we het integreren in de hoofdapplicatie.
