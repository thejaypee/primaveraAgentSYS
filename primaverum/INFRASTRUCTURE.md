# 🏗️ PrimaVerum Infrastructure Log

## 🖥️ Node: K11 NUC (Control Plane)
- **Hardware**: Intel NUC (K11)
- **Role**: Co-builder workstation. Runs primaverum, the Streamlit GUI (port 8501), and orchestrates don1/don2.
- **Access**: Local — this is where we work from.

## 🖥️ Node: don1 (The Trainer)
- **Hardware**: Jetson Orin Nano (8GB)
- **OS**: L4T R36 (JetPack 6.0/6.1)
- **Role**: Language-Logic Bridge / Voice Router
- **Access**: SSH alias `don1` (Certs integrated)
- **LLM Server**: Jetson Containers — vLLM container or `nano_llm`
- **Recommended Model**: NVIDIA Nemotron 3 Nano 9B — NVIDIA's own model for Orin Nano (~9 tok/s). Alternatively Mistral 3 via vLLM.
- **API**: OpenAI-compatible endpoint at `http://don1:8000/v1`
- **Details**:
  - TARGET_USERSPACE_LIB_DIR_PATH=/usr/lib/aarch64-linux-gnu/nvidia
  - KERNEL_VARIANT: oot
  - Enable "Super" mode in JetPack for performance boost
  - NVMe SSD strongly recommended for swap

## 🖥️ Node: don2 (The LogicModel)
- **Hardware**: Jetson Orin Nano (8GB)
- **OS**: L4T R36 (JetPack 6.0/6.1)
- **Role**: Pure Logic Core — Tabula Rasa
- **Access**: SSH alias `don2` (Certs integrated)
- **LLM Server**: Jetson Containers — `jetson-containers run $(autotag nano_llm)`
- **Recommended Models**: Smallest capable base model (not instruction-tuned) — this is the blank slate being trained
- **API**: nano_llm exposes OpenAI-compatible endpoint at `http://don2:8000/v1`
- **Details**:
  - Legacy Ollama installation present — **remove it, do not use it**
  - NVMe SSD strongly recommended for swap

## ☁️ Cloud: NVIDIA Developer API
- **Endpoint**: `https://integrate.api.nvidia.com/v1`
- **Role**: Heavy Thinking / Orchestration
- **Model**: `nvidia/llama-3.1-nemotron-70b-instruct`

## ⚙️ K11 as Congregation Point

K11 is not just the control plane — it is the **meeting ground**. All nodes congregate here through their harnesses. The harness is what gives a node a presence on K11. Without a harness, a node cannot be here.

```
K11 (congregation point)
  ├── don1 harness    → Trainer agent — don1 is present via primaverum
  ├── don2 harness    → LogicAgent — EMPTY, not yet built. Don2 cannot congregate yet.
  ├── AI Counsel      → deliberates here when called (planned)
  ├── documentAgent   → watches and records here (defined, not yet running)
  └── message bus     → signals between nodes (repos/local-* — started, not wired up)
```

**Don2's harness is the immediate gap.** Until it is built, don2 has no presence on K11. The LogicAgent in primaverum speaks *about* don2 but don2 itself is not here. Building the harness is what brings don2 into the congregation.

## ⚙️ Architecture: Hybrid Delegation
- **Local**: Symbolic synthesis and user chat.
- **Cloud**: High-order symbolic proofs and stability audits.

## 🕸️ Deployment Destination — meshOS Distributed Compute

Primaverum trains the LogicModel. meshOS is where it gets deployed.

The distributed compute network routes workloads to best-fit specialized agents. The LogicModel is being purpose-built as the **logic reasoning specialist** in that network. Once trained, it joins as a worker node — work requiring formal logic gets routed to it.

Every future specialized agent follows the same pattern: trained in a forge like primaverum, deployed into meshOS.

**Not using Exo** — meshOS uses its own orchestration layer, not Exo's distributed inference cluster.

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
