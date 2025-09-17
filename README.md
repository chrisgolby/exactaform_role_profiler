# Exactaform Role Profiler

Exactaform Role Profiler analyses a job description to surface a ranked blend of Gallup CliftonStrengths, values, behavioural interview prompts, and an explainability trail. It also offers an Ask Codex side-chat for “why” questions and context tweaks.

## Features

- Top five CliftonStrengths and values with score blend (keyword, semantic, role prior, context modifiers).
- Behaviour packs for every selection: why it matters, risk if overused, mitigation/interview probe, do-well indicators, and anti-patterns.
- Explainability panel linking scores back to JD phrases.
- Three behavioural interview questions tied to the ranked profile.
- Ask Codex chat to interrogate picks, explore “why not” queries, and test what-if adjustments (e.g. increase technical troubleshooting).
- Optional semantic boost with OpenAI embeddings when `LLM_DISABLED=false` and `OPENAI_API_KEY` is supplied.

UK English is used throughout.

## Getting started

### Backend

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Environment flags:

- `LLM_DISABLED=true` (default) keeps scoring fully local.
- Set `LLM_DISABLED=false` and provide `OPENAI_API_KEY` to enable OpenAI embedding calls.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 once both servers are running.

### Production build served by FastAPI

To run everything from a single, web-accessible process:

```bash
cd frontend
npm install
npm run build  # outputs to backend/static
cd ..
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Browse to http://localhost:8000 to use the compiled app alongside the API. The backend automatically serves the assets from `backend/static` when present.

### Docker

Alternatively, build a production container image that bundles the compiled frontend and FastAPI service:

```bash
docker build -t exactaform-role-profiler .
docker run -p 8000:8000 exactaform-role-profiler
```

The container exposes the app at http://localhost:8000.

## Running tests

```bash
pytest
```

## Acceptance test

With a job description containing “first point of contact”, “troubleshoot”, “escalate”, and “remain calm under pressure”, expect:

- Top Strengths: Empathy, Communication, Adaptability, Responsibility, Restorative.
- Top Values: Caring, Calm, Trustworthy, Friendly, Patient.
- Evidence chips referencing those phrases in the explainability panel.

## Project structure

- `backend/`: FastAPI app, scoring logic, behaviour packs, prompts, and tests.
- `frontend/`: React + Tailwind single-page app with form inputs, results panes, and Ask Codex chat.
