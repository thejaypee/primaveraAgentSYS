# 🏗️ PrimaVerum Infrastructure Log

## ⏱️ Current Status (as of now)

| Node | Tailscale IP | LLM Service | Status |
|------|--------------|-------------|--------|
| sauly-1 (K11) | 100.124.208.36 | N/A (control plane) | ✅ Active |
| don1 | 100.104.65.53 | port 8000 | ⚠️ Down — container not running |
| don2 | 100.101.70.84 | port 8000 | ⚠️ Down — container not running |

**Summary**: Tailscale fabric is operational. Both Jetson nodes are reachable. LLM services need to be started.

### Quick Start (from K11)

Run the service starter script:
```bash
./start-llm-services.sh
```

Or start manually:

**don1 (Trainer):**
```bash
ssh don1
cd ~/jetson-containers
./jetson-containers run nano_llm:24.7 python3 -m nano_llm.server \
    --api --model princeton-nlp/Sheared-LLaMA-2.7B --port 8000 --host 0.0.0.0
```

**don2 (LogicAgent):**
```bash
ssh don2
cd ~/jetson-containers
./jetson-containers run nano_llm:24.7 python3 -m nano_llm.server \
    --api --model TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T --port 8000 --host 0.0.0.0
```

**Verify:**
```bash
python3 diagnose_system.py
```

---

## 🖥️ Node: K11 / sauly-1 (Control Plane)
- **Hardware**: Intel NUC (K11)
- **Tailscale**: `100.124.208.36` (sauly-1)
- **Role**: Co-builder workstation. Runs primaverum, the Streamlit GUI (port 8501), and orchestrates don1/don2.
- **Access**: Direct — Linux dual-boot, this is where we work from.
- **Note**: Previous Windows install (`nucbox-k11`, 100.124.194.96) offline 17d.

## 🖥️ Node: don1 (The Trainer)
- **Hardware**: Jetson Orin Nano (8GB)
- **OS**: L4T R36 (JetPack 6.0/6.1)
- **Tailscale**: `100.104.65.53` (don1)
- **Role**: Language-Logic Bridge / Voice Router
- **Access**: SSH alias `don1` resolves via Tailscale (or `ssh don1@100.104.65.53`)
- **LLM Server**: Jetson Containers — vLLM container or `nano_llm`
- ** LLM API**: OpenAI-compatible endpoint at `http://don1:8000/v1` (via Tailscale MagicDNS)
- **Status**: ⚠️ Container not running — service unreachable on port 8000
- **Recommended Model**: NVIDIA Nemotron 3 Nano 9B — NVIDIA's own model for Orin Nano (~9 tok/s). Alternatively Mistral 3 via vLLM.
- **Details**:
  - TARGET_USERSPACE_LIB_DIR_PATH=/usr/lib/aarch64-linux-gnu/nvidia
  - KERNEL_VARIANT: oot
  - Enable "Super" mode in JetPack for performance boost
  - NVMe SSD strongly recommended for swap

## 🖥️ Node: don2 (The LogicModel)
- **Hardware**: Jetson Orin Nano (8GB)
- **OS**: L4T R36 (JetPack 6.0/6.1)
- **Tailscale**: `100.101.70.84` (don2)
- **Role**: Pure Logic Core — Tabula Rasa
- **Access**: SSH alias `don2` resolves via Tailscale (or `ssh don2@100.101.70.84`)
- **LLM Server**: Jetson Containers — `jetson-containers run $(autotag nano_llm)`
- ** LLM API**: OpenAI-compatible endpoint at `http://don2:8000/v1` (via Tailscale MagicDNS)
- **Status**: ⚠️ Container not running — service unreachable on port 8000
- **Recommended Models**: Smallest capable base model (not instruction-tuned) — this is the blank slate being trained
- **Details**:
  - NVMe SSD strongly recommended for swap

---

## ☁️ Cloud: NVIDIA Developer API
- **Endpoint**: `https://integrate.api.nvidia.com/v1`
- **Role**: Heavy Thinking / Orchestration
- **Model**: `nvidia/llama-3.1-nemotron-70b-instruct`

## 🧵 The Harness as Fabric

The harness is not a point-to-point connection. It is a **fabric** — it stretches across the entire distributed system, through the middle and all the geometry. Every container in the network connects to it through its own adapter. The fabric is what makes congregation possible.

```
                    [ HARNESS FABRIC ]
                   /        |         \
          don1-adapter  don2-adapter  future-adapters
              |              |
           don1           don2 (harness empty — not yet woven in)
```

**Containers are the unit.** Each node exposes its capabilities through a containerized adapter to the fabric. The harness fabric carries signals between them. No container talks directly to another — everything passes through the fabric.

**Surgical placement.** Each agent/container does not connect to the fabric arbitrarily — it enters at its best geometric position to interact with what it needs to interact with. The adapter is placed precisely where the agent's capabilities meet the fabric's signal flow. Wrong position = wrong interaction surface = wasted capability.

**The harness is multidimensional.** Via software, it can transport any model into the role of the agent it is operating. The model is not the agent — the harness is what gives it an agent identity, a position in the fabric, and a job. Swap the model behind the adapter, and the agent's presence in the congregation remains. This is the mechanism by which the LogicModel can be retrained, upgraded, or replaced without dismantling the fabric.

**Two dimensions the fabric bridges:**
- **Execution dimension** — where the work actually runs. RAM on don1, compute on a Windows/WSL machine, inference on the cloud, logic on don2. The work lives where the hardware is.
- **Presence dimension** — where the interaction is realized. K11 is the stage. Everything that happens across the network — regardless of where it executes — is presented, received, and experienced here.

The fabric connects these two dimensions. A process running in WSL on a Windows machine is present on K11 through its adapter. The user never sees the execution layer — they see the stage. K11 is the front end for the entire distributed system. All internet activity, all agent interaction, all input and output flows through this machine as the realization point. The computation may be anywhere. The experience is always here.

**Container system:** NVIDIA Workbench (`nvwb-cli`) is the candidate for container management across Jetson nodes. It has its own security model and CLI conventions — use `nvwb-cli` exclusively for container operations on don1/don2. Never raw Docker/podman on those nodes.

**Repository master record — MyBook NAS:**
All nodes pull from and push to the MyBook (NAS on local network, 192.168.2.x) as the master record. Two purposes:
1. Backup — all state lives on MyBook before anywhere else
2. Single source of truth — nodes sync to MyBook, not to each other directly

MyBook hostname not currently resolving — needs to be located on the local network (likely 192.168.2.89, .221, or .191) and configured.

**Message bus infrastructure (`~/repos/local-*`):**
A broker/dispatch/relay/parser/archive system was started as the fabric's signal layer. Not yet wired up. These repos are the congregation infrastructure — the internal communication layer between node adapters.

## ⚙️ K11 as Congregation Point — The Stage

K11 is not just the control plane — it is the **stage**. All interaction is realized here. All nodes congregate here through their harnesses. The harness is what gives a node a presence on K11. Without a harness, a node cannot be here.

Where something *runs* and where it *appears* are two different dimensions. K11 is the presence layer — the front end where all dimensions of the distributed system are experienced as one. The execution may be distributed across Jetson nodes, Windows/WSL, cloud, or RAM on any machine in the network. The stage is always K11.

```
K11 (congregation point)
  ├── don1 harness    → Trainer agent — don1 is present via primaverum (⚠️ container down)
  ├── don2 harness    → LogicAgent — don2 is present via primaverum (⚠️ container down)
  ├── AI Counsel      → deliberates here when called (planned)
  ├── documentAgent   → watches and records here (defined, not yet running)
  └── message bus     → signals between nodes (repos/local-* — started, not wired up)
```

**Current Gap:** Don1 and don2 are on Tailscale and reachable via SSH, but the LLM container services on port 8000 are not running. The harness fabric exists, but the adapters are not attached.

**Isolation principle — one container, one crash domain.** Every agent runs in its own container. No single agent failure can cascade and bring down the congregation. Each container is a fault boundary.

**Circuit breaker.** The AI Counsel is not just deliberative — it is the fallback layer. When an agent fails, the circuit breaker routes to the next best available agent from the Counsel. The Counsel always has a quorum as long as any member is running. Path: `~/ai-counsel/` — being built on K11 using Ollama (local K11 models, not Jetson-dependent). Resource-conscious: Counsel agents are lightweight deliberators, not heavy inference engines.

## ⚙️ Architecture: Hybrid Delegation
- **Local**: Symbolic synthesis and user chat.
- **Cloud**: High-order symbolic proofs and stability audits.

## 🕸️ Deployment Destination — meshOS Distributed Compute

Primaverum trains the LogicModel. meshOS is where it gets deployed.

The distributed compute network routes workloads to best-fit specialized agents. The LogicModel is being purpose-built as the **logic reasoning specialist** in that network. Once trained, it joins as a worker node — work requiring formal logic gets routed to it.

Every future specialized agent follows the same pattern: trained in a forge like primaverum, deployed into meshOS.

**Not using Exo** — meshOS uses its own orchestration layer, not Exo's distributed inference cluster.

---

## 🏛️ Planned Systems (not yet built)

| System | Path | Purpose | Status |
|--------|------|---------|--------|
| AI Counsel | `~/ai-counsel/` | Deliberative body + circuit breaker. High-stakes decisions, agent failover. Ollama on K11, isolated containers. | Blueprint defined |
| AI Academy | `~/ai-academy/` | Generalized training framework — what primaverum is for the LogicModel, for all agents. | Placeholder only |

---

## 🧬 Don1 Digital Twin Roadmap — NVIDIA ACE

**Reference**: https://github.com/NVIDIA/ACE

NVIDIA ACE is the suite for building digital humans with generative AI. It is the full stack for evolving don1 from a voice router into a true cognitive digital twin of the user.

### Relevant ACE Components for Don1

| Component | Role in Don1 |
|-----------|-------------|
| **Riva** | STT + TTS — don1's voice layer. Captures user speech, synthesizes don1's responses. |
| **ACE Agent** | Conversation + RAG workflows — the conversational intelligence layer of don1. |
| **Nemotron-3 4.5B** | Lightweight SLM — alternative to 9B for Orin Nano, tighter memory fit. |
| **Audio2Face** | Converts don1's audio output to facial animation — physical embodiment layer. |
| **AnimGraph** | Animation control — drives don1's avatar motion. |
| **Omniverse RTX Rendering** | Pixel streaming for don1's visual presence — connects to Omniverse for full avatar. |

### Evolution Path
1. **Now**: Don1 as text/logic bridge (primaverum)
2. **Next**: Riva voice layer — don1 speaks and listens natively
3. **Then**: ACE Agent replaces/augments the Trainer — richer conversational memory and RAG
4. **Later**: Audio2Face + Omniverse — don1 gets a face and physical embodiment
5. **Goal**: Don1 as a full cognitive + physical digital twin of the user — trained on their reasoning patterns, speaking in their voice, with their face
