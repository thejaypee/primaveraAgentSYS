# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the full sequential crew
crewai run

# Launch the Streamlit GUI (preferred for interactive sessions)
uv run run_gui
# or directly:
streamlit run src/primaverum/gui.py

# Dependency management
uv sync

# Training, testing, replay
crewai train -n <N> -f <file.json>
crewai test -n <N> -m <model>
crewai replay -t <task_id>

# Reset agent memories
crewai reset-memories -a
```

## Architecture

Primaverum is a NVIDIA-native CrewAI system designed to train a blank base model (don2) from zero through structured logical sessions. It is **not** an OpenAI project — all LLMs are NVIDIA or local NVIDIA-compatible endpoints.

### Hardware

| Node | Hardware | OS | Role |
|------|----------|----|------|
| don1 | Jetson Orin Nano 8GB | L4T R36 / JetPack 6.x (aarch64) | Trainer — Language-Logic Bridge |
| don2 | Jetson Orin Nano 8GB | L4T R36 / JetPack 6.x (aarch64) | LogicModel — Pure Logic Core (tabula rasa) |
| Cloud | NVIDIA Developer API | `https://integrate.api.nvidia.com/v1` | Heavy thinking / orchestration |

Don2 currently has Ollama installed. Migration to NVIDIA-native stack is planned.

### The Three LLMs (`crew.py`)

| Name | Model | Endpoint | Role |
|------|-------|----------|------|
| `heavy_thinker` | `nvidia/llama-3.1-nemotron-70b-instruct` | NVIDIA Cloud NIM | Cognitive heavy lifting — derives what to teach next |
| `don1_trainer` | `openai/local-trainer` | `$DON1_URL` (don1 node) | Trainer's default LLM — human-logic bridge |
| `don2_logic` | `openai/local-logic-model` | `$DON2_URL` (don2 node) | **Blank base NVIDIA model. Tabula rasa. This is what is being trained.** |

### The Two Agents

- **Trainer** (don1): Static function — always translates human language into formal logical precepts to feed into the mechanism. Over time it takes on an orchestrator/supervisor role over the LogicAgent it helped train.
- **LogicAgent** (don2): Harness for the blank model. A pure logician — strict symbolic input only, no emotional reasoning, no bad examples. Guards the purity of what gets integrated. Must have external tool access to make calls from anywhere (external APIs, on-chain data, external systems). A logician that can only reason internally is limited; this one has reach.

### The Three Sequential Tasks

1. **`agentLogicTrainingSession_proposal`** — Trainer runs with `heavy_thinker` LLM (override in code). Reads `LogicModel_Evolution_Log.md`, audits system stability, derives the next LogicRequirement.
2. **`LogicModel_integration`** — LogicAgent integrates the approved proof into don2's blank model. Verifies consistency.
3. **`agentLogicTrainingSession_documentation`** — Trainer updates `LogicModel_Evolution_Log.md` with the session results. This log is the system's memory of its own state — it determines what the next session teaches.

### Key Design Points

- The Trainer's LLM is **explicitly swapped** to `heavy_thinker` for the proposal task (`crew.py:60-63`). This is intentional — cloud-level intelligence does the derivation, local model handles communication.
- `LogicModel_Evolution_Log.md` is the cumulative training history. It grows with every session and feeds back into the next proposal. Do not delete it.
- The Streamlit GUI (`gui.py`) inserts a human approval gate between proposal and integration. The user can reject a proposal before it touches the LogicModel.
- Each session is a training pass. The system is designed for iterative, cumulative knowledge building — not one-shot execution.

### Environment Variables

```
NVIDIA_API_KEY=...          # Required for heavy_thinker (NVIDIA Cloud NIM)
DON1_URL=http://don1:8000/v1  # Default: don1 local node
DON2_URL=http://don2:8000/v1  # Default: don2 local node
```

## Design Philosophy

- **The human shapes the LogicModel.** The system's role is to receive the user's logic faithfully and integrate it — not to interpret, embellish, or decide what gets trained. The human is always available and is the source of truth.
- **Logic shapes logic.** What enters the LogicModel must be pure logic. No emotional reasoning, no corrupted examples, no noise. The LogicAgent's harness exists to enforce this. Reject anything that isn't formal logic before it touches don2.
- **The LogicAgent has external reach.** It is not sandboxed. It can query external systems, APIs, and blockchains from wherever it runs. Equip it with tools accordingly.
- **Primaverum is the forge, not the destination.** Once properly trained, the LogicModel leaves don2 and becomes the orchestrator of a separate system. Every session here is building toward that deployment — a logician capable of commanding other systems, not just accumulating proofs.
- **Don1 and Don2 are permanently tied.** Even after the LogicModel deploys elsewhere, the don1/don2 relationship persists. Don1 is always the user's voice to don2 — not metaphorically, literally: don1 runs NVIDIA TTS and STT so the human speaks, don1 translates to formal logic, don2 receives it as pure precept.
- **Don2 teaches don1 how to teach it.** As the LogicModel accumulates logic and grows more capable, it actively informs don1 how to better structure future inputs. The training relationship is bidirectional and continuous — don2 refines the quality of its own training by shaping don1's translation layer.
- **Two layers: outside and inside.** The user and Claude (this instance) are the co-builders — outside the system, designing and directing it. Don1 and Don2 are inside the system, running it.
- **Don1 is the membrane.** A hybrid local/cloud agent. It speaks to the user in natural spoken language via NVIDIA TTS/STT. It speaks to Don2 in pure formal logic only. It is the only bridge between the human world and Don2's logical world.
- **Don2 receives only from Don1.** Tabula rasa. It has no direct human interface. Everything that enters it has already been translated into formal logic by Don1.
- **This is a permanent three-way relationship: the human, don1, and don2.** Not a pipeline. Not session-based. Always active. The human provides intent; don1 renders it as logic and speaks it to don2; don2 grows and teaches don1 how to speak to it better. All three pull each other forward.

## Constraints

- **Never use `ChatOpenAI` or any raw OpenAI client.** Always use `crewai.LLM` or LiteLLM string shorthand (`"provider/model"`).
- Agent and task method names in `crew.py` must exactly match the keys in `agents.yaml` and `tasks.yaml`.
- Always add `# type: ignore[index]` when accessing config dicts in crew classes.
- The `openai/` prefix in local model names is LiteLLM syntax for OpenAI-compatible APIs — it does not mean OpenAI is being used.
