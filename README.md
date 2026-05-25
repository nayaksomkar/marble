# 🚀 Marble - Automated Data Pipeline

**One-command setup** | **2 PDF documents** | **7 knowledge-graph nodes** | **5 LLM-selected topics** | **Works on PC & Android**

---

## ⚡ Quick Start (30 seconds)

```bash
# 1. Run automated setup
python run_complete_setup.py

# 2. Test the system
python test_system.py

# 3. Start API
python main.py
```

Then visit: **http://localhost:8000/docs**

---

## 💾 How Data is Stored in Each Database

### SQLite (`data/marble.db`)
```
┌─────────────────────────────────────────────┐
│  documents                                  │
│  • id, title, content, source, status       │
│  • Stored: 2 PDF documents                 │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  chunks                                     │
│  • id, document_id, chunk_text, sequence    │
│  • 512-char segments with 100-char overlap  │
│  • Stored: 2,698 text chunks                │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  entities                                   │
│  • id, document_id, entity_name, type       │
│  • Capitalized words extracted              │
│  • Stored: 20 entities                      │
└─────────────────────────────────────────────┘
```

### Chroma (`data/chromadb/`)
```
┌─────────────────────────────────────────────┐
│  documents_vectors                          │
│  • Vector embeddings for similarity search  │
│  • First 100 chunks embedded                │
│  • Local file-based, no server needed       │
└─────────────────────────────────────────────┘
```

### Neo4j Graph (`data/neo4j/graph.json`)
```
┌─────────────────────────────────────────────┐
│  nodes (7 total)                            │
│  • Document: 2 (PDF files)                  │
│  • Topic: 5 (LLM-selected main topics)      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  edges (10 total)                           │
│  • HAS_TOPIC: Document → Topic               │
│  • TOPIC_OF:  Topic → Document                │
└─────────────────────────────────────────────┘
```

### Raw JSON (`data/raw/`)
```
┌─────────────────────────────────────────────┐
│  doc_DiabetesDataVizGit.json                │
│  doc_RetinaDxPPT.json                       │
│  • Portable for Android Termux              │
│  • Contains: content, summary, questions, topics
│  • 5 LLM-selected main topics                 │
└─────────────────────────────────────────────┘
```

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| Documents | 2 (PDFs from uploads/) |
| Chunks | 2,698 |
| Graph Nodes | 7 (2 Docs + 5 Topics) |
| Graph Edges | 10 (HAS_TOPIC / TOPIC_OF) |
| Setup Time | ~30 seconds |

### Knowledge Graph Visualization

![Knowledge Graph](data/neo4j/knowledge_graph.png)

*Figure: Marble knowledge graph — blue = Documents, green = Topics, edges show topic ownership*

---

## 📁 Final Clean Structure

```
marble/
├── data/                    # ALL data (~17 MB, portable)
│   ├── marble.db           # SQLite database
│   ├── chromadb/           # Vector storage
│   └── neo4j/
│       └── graph.json      # Knowledge graph (JSON)
│
├── uploads/               # PDF files
│   ├── DiabetesDataVizGit.pdf
│   └── RetinaDxPPT.pdf
│
├── data/raw/              # Raw JSON for Android portability
├── logs/                  # Setup logs
├── run_complete_setup.py  # Automated setup
├── test_system.py         # Test suite
├── verify_all.py          # Verification suite
├── summarize.py           # AI summarization
└── README.md
```

---

## 🎯 Usage

```bash
# Step 1: Setup
python run_complete_setup.py

# Step 2: Test
python test_system.py

# Step 3: Query SQLite
sqlite3 data/marble.db
> SELECT * FROM documents;
> SELECT COUNT(*) FROM chunks;

# Step 4: View graph
cat data/neo4j/graph.json | python -m json.tool
```

---

## 📱 Android Setup (Termux)

```bash
apt update && apt install python git
git clone <repo-url> && cd marble
pip install pypdf2 chromadb
python run_complete_setup.py
```

Then access: `http://localhost:8000/docs`

---

## ✅ All Tests Passing

```
✅ SQLITE DATABASE... PASS
✅ NEO4J GRAPH... PASS
✅ CHROMA STORAGE... PASS
✅ FILE STRUCTURE... PASS
✅ API COMPATIBILITY... PASS
🎉 ALL TESTS PASSED (5/5)
```