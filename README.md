# RAG API

A production-ready Retrieval-Augmented Generation (RAG) API built with FastAPI, ChromaDB, and Ollama, which is fully containerised and deployable with a single command.

---

## What It Does

Standard LLMs have a fixed knowledge cutoff and no awareness of your private data. This API wraps a local LLM with a vector database layer, enabling it to answer questions grounded in a custom, updatable knowledge base — without any fine-tuning or cloud API dependency.

Two endpoints expose the full RAG loop:

- **`POST /query`** — retrieve relevant context from the knowledge base, inject it into the prompt, and return a grounded answer from the LLM
- **`POST /add`** — embed and store new knowledge at runtime, persisting it to both the vector database and the backing file

---

## Architecture

```
User Request
     │
     ▼
 FastAPI App
     │
     ├─── /query ──► ChromaDB (similarity search)
     │                    │
     │               relevant context
     │                    │
     │               Ollama (tinyllama)
     │                    │
     │              grounded answer
     │                    │
     └─── /add ───► ChromaDB + knowledgebase.txt (persist)
```

**Request flow for `/query`:**
1. Query is sent to ChromaDB for cosine similarity search against stored embeddings
2. If the nearest document distance is ≤ 1 (i.e. meaningfully relevant), it is injected as context into the prompt
3. If no relevant document is found, the LLM answers from its own weights alone — preventing irrelevant context from degrading response quality
4. The LLM generates and returns a grounded answer

**Request flow for `/add`:**
1. New text is assigned a UUID and embedded into ChromaDB
2. The text is simultaneously appended to `knowledgebase.txt`, which is bind-mounted to the host — ensuring knowledge survives container restarts

---

## Stack

| Component | Role |
|---|---|
| **FastAPI** | REST API framework — async, auto-documented via Swagger |
| **ChromaDB** | Local vector database — stores and retrieves document embeddings |
| **Ollama** | Local LLM inference — runs `tinyllama` on the host machine |
| **Docker** | Containerises the FastAPI app and its dependencies |
| **Docker Compose** | Wires the app container to the host-resident Ollama service |
| **Uvicorn** | ASGI server — serves FastAPI in both dev and production |

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- [Ollama](https://ollama.com/) installed and running on the host

Pull the model before starting:
```bash
ollama pull tinyllama
```

### Run

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

Interactive API docs (Swagger UI): `http://localhost:8000/docs`

---

## API Reference

### `POST /query`

Query the knowledge base and get an LLM-generated answer.

| Parameter | Type | Description |
|---|---|---|
| `q` | `string` | The question to ask |

**Example:**
```bash
curl -X POST "http://localhost:8000/query?q=What+is+Kubernetes"
```

**Response:**
```json
{
  "answer": "Kubernetes is a container orchestration platform used to manage containers at scale."
}
```

**Context injection logic:** The API does not blindly inject retrieved documents into every prompt. ChromaDB returns a cosine distance score alongside each result — if the nearest document's distance exceeds `1.0`, the query is considered out-of-distribution relative to the knowledge base and no context is injected. This prevents irrelevant context from confusing the model.

---

### `POST /add`

Add new knowledge to the knowledge base at runtime.

| Parameter | Type | Description |
|---|---|---|
| `text` | `string` | The text to embed and store |

**Example:**
```bash
curl -X POST "http://localhost:8000/add?text=Airflow+is+a+workflow+orchestration+tool."
```

**Response:**
```json
{
  "status": "success",
  "message": "Content added to knowledge base",
  "id": "a3f1c2d4-..."
}
```

New knowledge is immediately available to subsequent `/query` calls and is persisted to `knowledgebase.txt` on the host via Docker bind mount — surviving container restarts without requiring a rebuild.

---

## Project Structure

```
.
├── app.py                  # FastAPI application — query and add endpoints
├── knowledgebase.txt                 # Knowledge base (plain text, bind-mounted)
├── Dockerfile              # Container definition for the FastAPI app
├── docker-compose.yaml     # Multi-service orchestration
└── README.md
```

---

## Design Decisions

**Why local inference with Ollama?**
No API keys, no usage costs, no data leaving the machine. The entire system runs offline once the model is pulled, which makes it suitable for private or air-gapped environments.

**Why ChromaDB?**
ChromaDB runs in-process with no separate service to manage, uses sensible defaults for embedding (sentence-transformers under the hood), and supports persistent storage, making it a practical choice for a self-contained RAG system.

**Why the distance threshold?**
A naive RAG implementation injects the top-k retrieved documents unconditionally. This actively degrades LLM output when the query is out-of-distribution relative to the knowledge base. The `distance > 1.0` guard ensures context is only injected when it is genuinely relevant.

**Why bind-mount `knowledgebase.txt`?**
The `/add` endpoint writes new knowledge to both ChromaDB and `knowledgebase.txt`. Mounting the file to the host means the knowledge base accumulates across container restarts, without needing a persistent volume for the entire database directory.

---

## Requirements

```
fastapi
uvicorn
ollama
chromadb
```
