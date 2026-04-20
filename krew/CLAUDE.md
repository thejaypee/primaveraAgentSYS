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
├── builder-krewe/                  # Code-generation crew (legacy CrewAI)
│   ├── src/builderkrewe/
│   │   ├── config/agents.yaml      # Agent definitions
│   │   ├── config/tasks.yaml       # Task definitions
│   │   ├── crew.py                 # @CrewBase assembly
│   │   ├── main.py
│   │   └── tools/custom_tool.py
│   ├── output/dashboard/           # Live hive dashboard (the primary running app)
│   │   ├── backend.py              # FastAPI server — port 8080
│   │   ├── index.html              # Dark UI, responsive % layout, auto-refresh 30s
│   │   └── requirements.txt
│   ├── GEMINI.md                   # CrewAI reference — read before writing CrewAI code
│   └── pyproject.toml
├── research-krewe/                 # Research crew (legacy CrewAI)
│   ├── src/research_crew/
│   │   ├── crew.py                 # OllamaWebSearch + OllamaWebFetch custom tools
│   │   └── ...
│   └── pyproject.toml
├── commands.md                     # Full command reference
└── (krewe/ hive router — aspirational, not yet implemented)
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
# Always kill existing instance before starting a new one
lsof -i :8080 -t | xargs -r kill -9; sleep 1
cd builder-krewe/output/dashboard && python3 backend.py &
# Open http://localhost:8080
```

**Topology layout rule:** every connector (horizontal and vertical) uses the single constant `GAP = 'min(4vw,48px)'` via `hline` and `vline`. Never use a custom size. Add new rows and nodes by reusing these variables — the topology rebalances automatically.

The dashboard auto-refreshes every 30s. It discovers nodes via `tailscale status --json`, pings all peers in parallel, and SSH-queries hardware for known hosts. Jetson nodes (don1, don2) use `tegrastats` for GPU/RAM/power; K11 uses AMD sysfs at `/sys/class/drm/card1/device/`.

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

## Hive Infrastructure (Design — not yet implemented)

Planned capability-based task router: nodes publish vectors (memory, GPU, models), router scores and dispatches to lowest-cost fit. No static agent-to-node mapping.

### Planned dependencies
- **Redis**: node registry (`krewe:nodes` hash), pub/sub for results and heartbeats
- **Tailscale**: mesh between K11, saulynode, don1, don2, DESKTOP-BVKF4TE; SSH key `~/.ssh/id_ed25519`, user `admin`
- **`/krewe_shared/`**: Syncthing/NFS for task checkpoints

### Known SSH aliases (in `backend.py:HiveService.SSH_HOSTS`)
| IP | Alias | Type |
|---|---|---|
| 100.104.65.53 | don1 | Jetson Orin Nano Super |
| 100.101.70.84 | don2 | Jetson Orin Nano Super |
| 100.85.15.80 | saulynode | Linux |
| 100.96.141.26 | wsl | Linux (WSL) |

---

## Configuration

Both projects read from `.env` (not committed):

```
MODEL=<litellm-compatible model string>
API_BASE=<LLM API endpoint>
```

`MODEL` uses LiteLLM syntax (e.g. `ollama/kimi-k2.5:cloud`). The `openai/` prefix is **LiteLLM routing syntax**, not the OpenAI API.
