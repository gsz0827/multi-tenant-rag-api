# Multi-Tenant RAG Knowledge Base

A multi-tenant RAG knowledge base system built with **FastAPI**, **PostgreSQL + pgvector**, **Redis**, **Celery**, and **React + Vite**.

The project supports user authentication, knowledge base management, document upload, asynchronous document ingestion, vector storage, RAG-based question answering, and a simple frontend management interface.

---

## Features

### Backend
- User authentication with JWT
- Multi-tenant knowledge base management
- Document upload
- Text extraction and sanitization
- Document chunking
- Embedding generation
- Vector storage with PostgreSQL + pgvector
- Asynchronous document ingestion with Celery
- Redis as Celery broker/result backend
- Single document ingestion
- Batch document ingestion
- Single document cancellation and retry
- Batch cancellation and retry
- Document ingestion status tracking
- RAG question answering
- Source chunk return for answer traceability

### Frontend
- Login and logout
- Persistent login state using access token
- Knowledge base creation
- Knowledge base selection
- Document upload
- Document list
- Document ingestion status display
- Auto polling for document status
- Single document operations:
  - ingest
  - cancel
  - retry
  - delete
- Batch operations:
  - batch ingest
  - batch cancel
  - batch retry
- Knowledge base question answering
- Source references display

---

## Tech Stack

### Backend
- Python 3.10+
- FastAPI
- SQLAlchemy
- PostgreSQL + pgvector
- Redis
- Celery
- JWT authentication

### Frontend
- React
- TypeScript
- Vite
- Axios

---

## Project Structure

```text
.
├── app
│   ├── api                 # FastAPI route modules
│   ├── core                # Config, security and status constants
│   ├── db                  # Database session and base models
│   ├── models              # SQLAlchemy models
│   ├── schemas             # Pydantic schemas
│   ├── services            # Business logic
│   ├── worker              # Celery app and tasks
│   └── main.py             # FastAPI application entry
│
├── frontend
│   ├── src
│   │   ├── api.ts          # Frontend API wrapper
│   │   ├── App.tsx         # Main frontend page
│   │   └── App.css         # Frontend styles
│   ├── vite.config.ts
│   └── package.json
│
├── requirements.txt
└── README.md
````

---

## Requirements

### Backend

* Python 3.10+
* PostgreSQL with pgvector extension
* Redis
* pip dependencies from `requirements.txt`

### Frontend

* Node.js 20.19+ or 22.12+
* npm

---

## Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/rag_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
API_PREFIX=/api
```

Adjust values according to your local environment.

---

## Database Setup

1. Ensure PostgreSQL is running.
2. Enable `pgvector` extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

3. Initialize tables according to the models in `app/models` (or use migrations if added).

---

## Backend Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start Redis:

```bash
redis-server
```

4. Start FastAPI backend:

```bash
uvicorn app.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`
Swagger API docs: `http://127.0.0.1:8000/docs`

---

## Celery Worker

Start the worker to handle document ingestion tasks:

```bash
celery -A app.worker.celery_app.celery_app worker -Q ingestion --loglevel=info
```

---

## Frontend Setup

1. Enter frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start development server:

```bash
npm run dev -- --host 0.0.0.0
```

Frontend URL: `http://localhost:5173` (or `http://<VM_IP>:5173` if using a VM)

The frontend proxies `/api` requests to the backend automatically.

---

## Usage Flow

1. Login via frontend.
2. Create or select a knowledge base.
3. Upload documents (.txt, .pdf, .docx).
4. Single or batch document ingestion.
5. Polling shows document status: `pending`, `queued`, `processing`, `completed`, `failed`, `cancelled`.
6. Ask questions in the knowledge base QA section.
7. Answers include source references from ingested documents.

---

## Main API Endpoints

* **Authentication:** `POST /api/auth/login`
* **Knowledge Bases:** `GET/POST /api/knowledge-bases`
* **Documents:**

  * `GET /api/documents?knowledge_base_id={id}`
  * `POST /api/documents/upload`
  * `DELETE /api/documents/{document_id}`
* **Single Document Ingestion:**

  * `POST /api/documents/{document_id}/prepare-async`
  * `POST /api/documents/{document_id}/cancel-ingestion`
  * `POST /api/documents/{document_id}/retry-ingestion`
  * `GET /api/documents/{document_id}/ingestion-status`
* **Batch Ingestion:**

  * `POST /api/documents/prepare-batch-async`
  * `POST /api/documents/cancel-batch-ingestion`
  * `POST /api/documents/retry-batch-ingestion`
  * `GET /api/documents/ingestion-status-batch`
* **RAG Question Answering:** `POST /api/rag/ask`

---

## Notes / Troubleshooting

* **Axios errors:** Ensure `npm install` was run inside `frontend`.
* **Queued documents:** Ensure Celery worker is running on `ingestion` queue.
* **No chunks / no answers:** Ensure documents are ingested (`completed` status) before asking questions.
* **Permissions:** Creating knowledge bases requires the user to belong to the specified organization.

---

## Current MVP Status

* Complete backend + frontend RAG workflow
* Login / logout
* Knowledge base creation
* Document upload and ingestion
* RAG question answering with source references
* Frontend management page

---

## Next Improvements

* Document pagination
* Streaming answers
* Chat history
* Docker Compose deployment
* Production monitoring and logging
* Role-based access control

```