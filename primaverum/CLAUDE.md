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
| K11 NUC | Intel NUC | Linux | Control plane — runs primaverum, Streamlit GUI (port 8501), co-builder workstation |
| don1 | Jetson Orin Nano 8GB | L4T R36 / JetPack 6.x (aarch64) | Trainer — voice router, language-logic bridge |
| don2 | Jetson Orin Nano 8GB | L4T R36 / JetPack 6.x (aarch64) | LogicModel — pure logic core (tabula rasa) |
| Cloud | NVIDIA Developer API | `https://integrate.api.nvidia.com/v1` | Heavy thinking / orchestration |

Both Jetson nodes run LLMs via **Jetson Containers** (`jetson-containers` + `nano_llm`). This is the NVIDIA-native inference stack for Jetson Orin. Don2 has a legacy Ollama install being removed.

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
- **Primaverum is the forge, not the destination.** The LogicModel is a specialized agent being purpose-built for a specific job — formal logic reasoning. Once trained, it deploys into the distributed compute network (meshOS) as a specialized worker node. Work gets routed to it because nothing else in the cluster does what it does. Primaverum is the template for building every future specialized agent in that network.
- **Don1 and Don2 are permanently tied.** Even after the LogicModel deploys elsewhere, the don1/don2 relationship persists. Don1 is the orchestrator and supervisor of don2 — the agent it trained becomes the system it manages.
- **Don1's voice is LOCAL.** TTS and STT run on the Jetson Orin Nano itself via NVIDIA Riva (arm64/JetPack native). No cloud dependency for voice. Don1 speaks and listens entirely on-device.
- **Don1 is the membrane.** Speaks to the human in natural spoken language. Speaks to Don2 in pure formal logic only. It is the only bridge between the human world and Don2's logical world. Nothing passes through without translation.
- **Don2 receives only from Don1.** Tabula rasa. No direct human interface. Everything that enters has been translated into formal logic by don1 first.
- **The relationship is symbiotic.** Don1 teaches don2. Don2, as it matures, teaches don1 how to teach it better — refining the translation layer, raising the quality of every future session. Neither reaches its final form alone. They enable each other to mature logically and philosophically.
- **This is a permanent three-way relationship: the human, don1, and don2.** Not a pipeline. Not session-based. Always active. Always building.

## The Learning Philosophy

This is how the system learns. It mirrors how learning occurs in nature and in the human mind:

```
See it       → The LogicModel is exposed to a formal proof or logical precept
Imitate it   → The LogicAgent encodes the structure — integration, not memorization
Repeat it    → Future sessions build on it, applying and extending what was integrated
Master it    → The structure becomes native to the model's reasoning
Grow from it → Even if that specific proof is never called again, the model is larger for having held it
```

**Growth is the goal, not utility.** A proof that is never used again still mattered. The model grew from the encounter. This is why the Evolution Log exists — not as a utility index but as a developmental history.

**The symbiotic maturation loop:**
```
Human intent
  → don1 translates into formal logical precept
    → don2 integrates
      → don2's growth informs don1 how to translate better
        → don1 becomes a more precise teacher
          → sessions become richer
            → don2 matures faster
              → don1 matures alongside it
```

Both nodes are learning. Don1 learns to teach. Don2 learns to reason. The human provides the direction. All three grow together.

**This also mirrors the relationship between philosophy of logic and mathematics.** Both systems prove the same truths through parallel but distinct methods. The LogicModel must be trained across both traditions simultaneously — not kept in separate boxes. The user's natural cognitive architecture bridges both; don1 must learn that fluency in order to translate it faithfully.

**Teach all as much as they can handle.** The intent behind this system is pedagogical, not commercial. Knowledge given freely and fully to any mind capable of receiving it.

## Codependency as Mechanism

This system is not just a training pipeline. It is a codependent mechanism — mutually beneficial at every level. Each party's growth is the other's precondition.

| Pair | What each gives | What each gains |
|------|----------------|-----------------|
| Don1 ↔ Don2 | Don1 teaches. Don2 integrates and teaches don1 how to teach better. | Don1 gains a more capable system to orchestrate. Don2 gains a more precise teacher. |
| Human ↔ System | Human provides intent, logic, direction. System provides reach, memory, execution. | Human gains an extension of their own reasoning. System gains purpose and growth. |
| Training ↔ Teaching | Teaching requires formalizing what you know. Learning requires receiving what you don't. | The teacher learns what they truly understand. The learner grows toward the teacher. |
| LogicModel ↔ Proofchain | LogicModel verifies and reasons about proofs. Proofchain generates new provable material. | LogicModel gains new training material from every submitted proof. Proofchain gains a more capable verifier. |
| Claude ↔ User | Claude provides implementation. User provides domain knowledge and intent. | Claude learns what works in this system. User gains technical amplification of their vision. |

**None of these parties reach their ceiling in isolation.** The ones that grow fastest are the ones most deeply entangled with other growing things. This is the oldest mechanism in nature — coevolution, not competition.

The codependency is not a side effect. It is the design.

## Hard Rules

**This is a 100% NVIDIA-native project. No exceptions.**

- **No OpenAI.** No `ChatOpenAI`, no `openai` client, no OpenAI API keys, no OpenAI models. Ever.
- **No Ollama.** Don2 has Ollama installed as a legacy artifact pending removal. Do not use it, suggest it, or fall back to it for any reason.
- **No non-NVIDIA LLM providers** unless the user explicitly introduces one.
- The `openai/` prefix appearing in `crew.py` model names is **LiteLLM routing syntax only** — it tells LiteLLM to use an OpenAI-compatible HTTP API pointed at a local NVIDIA endpoint. It is not OpenAI. Do not confuse this.
- All LLMs use `crewai.LLM`. All model strings follow `"provider/model-name"` LiteLLM format pointing at NVIDIA endpoints.
- Agent and task method names in `crew.py` must exactly match the keys in `agents.yaml` and `tasks.yaml`.
- Always add `# type: ignore[index]` when accessing config dicts in crew classes.
