# 🏗️ PrimaVerum Infrastructure Log

## 🖥️ Node: K11 NUC (Control Plane)
- **Hardware**: Intel NUC (K11)
- **Role**: Co-builder workstation. Runs primaverum, the Streamlit GUI (port 8501), and orchestrates don1/don2.
- **Access**: Local — this is where we work from.

## 🖥️ Node: don1 (The Trainer)
- **Hardware**: Jetson Orin Nano (8GB)
- **OS**: L4T R36 (JetPack 6.0/6.1)
- **Role**: Language-Logic Bridge
- **Access**: SSH alias `don1` (Certs integrated)
- **Details**: 
  - TARGET_USERSPACE_LIB_DIR_PATH=/usr/lib/aarch64-linux-gnu/nvidia
  - KERNEL_VARIANT: oot
  - Status: Clean L4T, ready for NVIDIA Native stack.

## 🖥️ Node: don2 (The LogicModel)
- **Hardware**: Jetson Orin Nano (8GB)
- **OS**: L4T R36 (JetPack 6.0/6.1)
- **Role**: Pure Logic Core
- **Access**: SSH alias `don2` (Certs integrated)
- **Details**:
  - Contains a legacy Ollama installation. **This is being removed and replaced with NVIDIA-native stack. Ollama is not used by primaverum.**

## ☁️ Cloud: NVIDIA Developer API
- **Endpoint**: `https://integrate.api.nvidia.com/v1`
- **Role**: Heavy Thinking / Orchestration
- **Model**: `nvidia/llama-3.1-nemotron-70b-instruct`

## ⚙️ Architecture: Hybrid Delegation
- **Local**: Symbolic synthesis and user chat.
- **Cloud**: High-order symbolic proofs and stability audits.
