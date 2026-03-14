# Tracer — Frontend

Next.js 16 + React 19 web UI for Tracer. Proxies all `/api/*` requests to the FastAPI backend running on `localhost:8000`.

---

## Prerequisites

### 1. Install Node.js and npm

If you have never installed Node.js before, use the official installer from the Node.js website. npm is included automatically with Node.js, so you do not need to install it separately.

**Direct download only:**

1. Go to https://nodejs.org
2. Download the **LTS** version
3. Run the installer and keep the default options
4. When the installer finishes, open a new terminal window

**Verify the install:**
```bash
node --version
npm --version
```

You should see:

- `node` version `v20.x.x` or higher
- `npm` version `9.x.x` or higher

If either command says it is not found, close the terminal, open it again, and rerun the commands.

### 2. FastAPI backend

The backend must be running on `localhost:8000` before starting the frontend. See the root [`README.md`](../README.md) for backend setup.

---

## Setup

```bash
# From the repo root, enter the frontend directory
cd frontend

# Download the frontend dependencies
npm install
```

---

## Running

### Development (hot reload)

```bash
npm run dev
```

Opens at **http://localhost:3000**. API calls are proxied to `http://localhost:8000`.

> Both the frontend (`npm run dev`) and backend (`uvicorn server:app --reload --port 8000`) must be running at the same time.

### Production build

```bash
npm run build
npm run start
```

---

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx        # Root layout, dark theme, fonts
│   ├── page.tsx          # Main page — sidebar + run form + artifact view
│   └── globals.css       # Tailwind + CSS variables (dark navy theme)
├── components/
│   ├── AppSidebar.tsx    # Collapsible sidebar with run history + filters
│   ├── ArtifactView.tsx  # Displays generated diagram + collapsible files
│   ├── HistoryItem.tsx   # Single history entry in the sidebar
│   └── RunForm.tsx       # New run form — strategy, model, input, generate
├── lib/
│   ├── api.ts            # Typed fetch wrappers for all backend endpoints
│   └── types.ts          # Shared TypeScript types (Run, Example, Artifacts)
└── components/ui/        # shadcn/ui primitives
```

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Next.js | 16 | Framework + API proxy |
| React | 19 | UI |
| Tailwind CSS | 4 | Styling |
| shadcn/ui | latest | UI components |
| TypeScript | 5 | Type safety |

---

## API Proxy

`next.config.ts` rewrites `/api/*` → `http://localhost:8000/api/*`, so the frontend never needs the backend URL hardcoded — all fetch calls use relative `/api/...` paths.

Key endpoints used:

| Endpoint | Description |
|----------|-------------|
| `GET /api/examples` | List available example systems |
| `GET /api/examples/{key}/description` | Fetch full description for an example |
| `POST /api/generate` | Stream SSE generation progress + result |
| `GET /api/history` | List all past runs |
| `GET /api/artifacts/{folder}` | Get artifact file paths for a run |
| `POST /api/render-mermaid` | Render a raw Mermaid diagram (no LLM) |

---

## Environment

No `.env` file is needed for the frontend. All configuration lives in the backend (API keys, model providers). See [`../README.md`](../README.md) and [`../OPENROUTER_SETUP.md`](../OPENROUTER_SETUP.md).
