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

## ⚙️ Architecture: Hybrid Delegation
- **Local**: Symbolic synthesis and user chat.
- **Cloud**: High-order symbolic proofs and stability audits.
