# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Krewe — Distributed Hive Architecture

The Hive is a **capability-based distributed agent swarm**. A Pixel phone and a NUC are indistinguishable — both publish capability vectors, the router schedules to whichever node meets requirements at lowest cost.

- **Hive Layer**: Router/Scheduler/Registry — logical resource fabric
- **Compute Layer**: Physical devices as interchangeable capacity
- **Key Insight**: No static agent-to-node mapping. Agent runs on whatever node has resources.

## Repository Layout

```
krew/
├── builder-krewe/                  # Code-generation crew (legacy, to be hive-ified)
│   ├── src/builderkrewe/
│   │   ├── config/agents.yaml
│   │   ├── config/tasks.yaml
│   │   ├── crew.py
│   │   ├── main.py
│   │   └── tools/custom_tool.py
│   ├── output/dashboard/           # Generated dashboard (running app)
│   │   ├── backend.py              # FastAPI server (port 8080)
│   │   ├── index.html
│   │   └── requirements.txt
│   ├── knowledge/user_preference.txt
│   ├── GEMINI.md                   # Comprehensive CrewAI reference — read before writing CrewAI code
│   └── pyproject.toml
├── research-krewe/                 # Research crew (legacy, to be hive-ified)
│   ├── src/research_crew/
│   │   ├── config/agents.yaml
│   │   ├── config/tasks.yaml
│   │   ├── crew.py                 # Includes OllamaWebSearch, OllamaWebFetch tools
│   │   ├── main.py
│   │   └── tools/custom_tool.py
│   ├── output/report.md
│   ├── knowledge/user_preference.txt
│   ├── GEMINI.md
│   └── pyproject.toml
├── krewe/                          # WIP: Hive router, registry, distributed scheduler
│   ├── hive_router.py              # FastAPI router (port 50051) — capability-based task dispatch
│   └── orchestrator.py             # Local thread-pool orchestrator (6 agents, in-memory)
├── deploy_all.sh                   # Deploy workers to Tailscale nodes
├── deploy_worker.sh                # rsync + SSH worker start for a single node
├── commands.md                     # Full command reference
└── krew_shared/                    # Shared storage (Syncthing/NFS) — task checkpoints
```

Each sub-project is a self-contained Python package managed with `uv`.

---

## Commands

Run from inside the sub-project directory (`cd builder-krewe` or `cd research-krewe`).

```bash
uv sync                                  # install dependencies
crewai run                               # run the crew
python -m builderkrewe.main              # builder-krewe entry point
python -m research_crew.main             # research-krewe entry point
crewai train <n_iterations> <filename>   # train
crewai test                              # evaluate
crewai replay -t <task_id>              # replay from task
crewai reset-memories                    # wipe memory
run_with_trigger '<JSON_PAYLOAD>'        # run with remote trigger payload
```

### Dashboard

```bash
# Always kill existing instance before starting
pkill -f "python3 backend.py"; sleep 1
cd builder-krewe/output/dashboard && python3 backend.py &
# Open http://localhost:8080
```

---

## Architecture

Both legacy crews follow the same CrewAI pattern:

1. **`config/agents.yaml`** — agent definitions (role, goal, backstory)
2. **`config/tasks.yaml`** — task definitions (description, expected_output, agent, output_file)
3. **`crew.py`** — assembles via `@CrewBase`, `@agent`, `@task`, `@crew` decorators
4. **`main.py`** — `run()`, `train()`, `test()`, `replay()`, `run_with_trigger()`

Tasks execute **sequentially**. The primary editing surface is `agents.yaml` and `tasks.yaml`.

---

## builder-krewe

**Agents** (6): `senior_backend_engineer`, `frontend_developer`, `qa_reviewer`, `requirements_analyst`, `ai_coder`, `tool_validator`

**Tasks** (6):
| Task | Output |
|---|---|
| `backend_development_task` | Backend API code |
| `frontend_development_task` | Frontend dashboard code |
| `assembly_and_review_task` | `output/dashboard/` |
| `analyze_tool_requirements_task` | Tool spec |
| `generate_tool_code_task` | Tool implementation |
| `test_and_validate_task` | `coding-tools/` |

Default topic: `"AI LLMs"` (in `main.py:run()`).

---

## research-krewe

**Agents** (2): `researcher`, `analyst`

**Tasks** (2):
| Task | Output |
|---|---|
| `research_task` | Raw research findings |
| `analysis_task` | `output/report.md` |

`crew.py` defines `OllamaWebSearch` and `OllamaWebFetch` — custom tools defined in `crew.py`, used by the researcher agent.

Default topic: `"Artificial Intelligence in Healthcare"` (in `main.py:run()`).

---

## Hive Infrastructure (WIP)

### hive_router.py — FastAPI on port 50051
Routes tasks to the best available node by scoring candidates on memory, cost, and latency.

Key endpoints: `/submit` (TaskRequest), `/nodes`, `/health`, `/parse`, `/verify`

Node registry stored in Redis hash `krewe:nodes`. Workers heartbeat every 10s.

### orchestrator.py — Local orchestrator
Thread-pool executor (max 6 workers), in-memory agent registry with per-agent LLM assignments. Handles agent dependency gates and inter-agent message queues.

### Infrastructure dependencies
- **Redis**: node registry, pub/sub for task results and heartbeats
- **Tailscale**: mesh network between nodes, latency target <10ms, SSH deployment
- **`/krewe_shared/`**: Syncthing or NFS mount for task checkpoints (written every 30s)

---

## Configuration

Both projects read from `.env` (not committed):

```
MODEL=<litellm-compatible model string>
API_BASE=<LLM API endpoint>
```

`MODEL` uses LiteLLM syntax (e.g. `ollama/kimi-k2.5:cloud`). The `openai/` prefix is **LiteLLM routing syntax**, not the OpenAI API.
