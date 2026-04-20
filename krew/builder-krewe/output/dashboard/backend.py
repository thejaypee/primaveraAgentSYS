import json
import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
import psutil
import docker

DASHBOARD_DIR = Path(__file__).parent


class DockerService:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
        except docker.errors.DockerException:
            self.client = None

    def get_running_containers(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            return [
                {
                    "id": c.short_id,
                    "name": c.name,
                    "image": c.image.tags[0] if c.image.tags else "unknown",
                    "status": c.status,
                    "ports": dict(c.ports),
                }
                for c in self.client.containers.list()
            ]
        except Exception:
            return []


class NetworkService:
    def get_all_interfaces(self) -> List[Dict[str, Any]]:
        import socket
        result = []
        for name, addresses in psutil.net_if_addrs().items():
            entry = {"interface": name, "addresses": []}
            for addr in addresses:
                if addr.family == socket.AF_INET:
                    entry["addresses"].append({"ip": addr.address, "netmask": addr.netmask})
                elif addr.family == psutil.AF_LINK:
                    entry["addresses"].append({"mac": addr.address})
            result.append(entry)
        return result


def _local_containers() -> List[Dict[str, Any]]:
    try:
        client = docker.from_env()
        client.ping()
        return [
            {"name": c.name, "image": c.image.tags[0] if c.image.tags else "unknown", "status": c.status}
            for c in client.containers.list()
        ]
    except Exception:
        return []


def _local_hardware() -> Dict[str, Any]:
    cpu_line = ""
    with open("/proc/cpuinfo") as f:
        for line in f:
            if "model name" in line:
                cpu_line = line.split(":", 1)[1].strip()
                break
    cores = os.cpu_count() or 0
    mem = psutil.virtual_memory()
    ram = f"{mem.total / 1024**3:.1f}GB"
    disk = psutil.disk_usage("/")
    disk_str = f"{disk.total / 1024**3:.0f}G"

    hw: Dict[str, Any] = {"cpu": cpu_line, "cores": cores, "ram": ram, "disk": disk_str,
                          "containers": _local_containers()}

    # AMD GPU via sysfs
    amd_busy = Path("/sys/class/drm/card1/device/gpu_busy_percent")
    amd_vram_used = Path("/sys/class/drm/card1/device/mem_info_vram_used")
    amd_vram_total = Path("/sys/class/drm/card1/device/mem_info_vram_total")
    if amd_busy.exists():
        try:
            util = int(amd_busy.read_text().strip())
            vram_used = int(amd_vram_used.read_text().strip()) // 1024**2
            vram_total = int(amd_vram_total.read_text().strip()) // 1024**2
            hw["gpu"] = "Radeon 780M (integrated)"
            hw["gpu_util_pct"] = util
            hw["gpu_vram_used_mb"] = vram_used
            hw["gpu_vram_total_mb"] = vram_total
        except Exception:
            pass

    return hw


def _parse_tegrastats(line: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    m = re.search(r"RAM (\d+)/(\d+)MB", line)
    if m:
        result["ram_used_mb"] = int(m.group(1))
        result["ram_total_mb"] = int(m.group(2))
    m = re.search(r"GR3D_FREQ (\d+)%", line)
    if m:
        result["gpu_util_pct"] = int(m.group(1))
    m = re.search(r"gpu@([\d.]+)C", line)
    if m:
        result["gpu_temp_c"] = float(m.group(1))
    m = re.search(r"VDD_IN ([\d]+)mW", line)
    if m:
        result["power_mw"] = int(m.group(1))
    return result


class HiveService:
    SSH_HOSTS = {
        "100.104.65.53":  "don1",
        "100.101.70.84":  "don2",
        "100.85.15.80":   "saulynode",
        "100.96.141.26":  "wsl",
        "100.110.149.48": "sauly-SuiPlay0X1",
    }
    JETSON_IPS = {"100.104.65.53", "100.101.70.84"}
    AMD_IPS    = {"100.110.149.48"}
    EXCLUDE_HOSTS = {"meinShafft", "stats"}

    def _ssh_hardware(self, host_alias: str, ip: str) -> Dict[str, Any]:
        if ip in self.JETSON_IPS:
            return self._ssh_jetson(host_alias)
        if ip in self.AMD_IPS:
            return self._ssh_amd(host_alias)
        cmd = (
            "cpu=$(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | xargs); "
            "cores=$(nproc); "
            "ram=$(free -m | awk 'NR==2{printf \"%.1fGB\", $2/1024}'); "
            "disk=$(df -h / | awk 'NR==2{print $2}'); "
            "gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || echo ''); "
            "ctrs=$(docker ps --format '{{.Names}}:::{{.Image}}:::{{.Status}}' 2>/dev/null | tr '\\n' ';;' || echo ''); "
            "echo \"$cpu|$cores|$ram|$disk|$gpu|$ctrs\""
        )
        try:
            out = subprocess.check_output(
                ["ssh", "-o", "ConnectTimeout=3", "-o", "BatchMode=yes", host_alias, cmd],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            cpu, cores, ram, disk, gpu, ctrs_raw = out.split("|", 5)
            result: Dict[str, Any] = {"cpu": cpu, "cores": int(cores), "ram": ram, "disk": disk}
            if gpu:
                result["gpu"] = gpu
            containers = []
            for entry in ctrs_raw.split(";;"):
                entry = entry.strip()
                if entry:
                    parts = entry.split(":::")
                    if len(parts) == 3:
                        containers.append({"name": parts[0], "image": parts[1], "status": parts[2]})
            result["containers"] = containers
            return result
        except Exception:
            return {}

    def _ssh_jetson(self, host_alias: str) -> Dict[str, Any]:
        cmd = (
            "cpu=$(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | xargs); "
            "cores=$(nproc); "
            "disk=$(df -h / | awk 'NR==2{print $2}'); "
            "model=$(cat /proc/device-tree/model 2>/dev/null | tr -d '\\0' || echo 'Jetson'); "
            "teg=$(tegrastats 2>&1 | head -1); "
            "ctrs=$(docker ps --format '{{.Names}}:::{{.Image}}:::{{.Status}}' 2>/dev/null | tr '\\n' ';;' || echo ''); "
            "echo \"$cpu|$cores|$disk|$model|$teg|$ctrs\""
        )
        try:
            out = subprocess.check_output(
                ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", host_alias, cmd],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            cpu, cores, disk, model, teg, ctrs_raw = out.split("|", 5)
            hw: Dict[str, Any] = {
                "cpu": cpu or model,
                "cores": int(cores),
                "disk": disk,
                "gpu": "Ampere GPU (Jetson Orin Nano Super)",
            }
            teg_stats = _parse_tegrastats(teg)
            if teg_stats.get("ram_total_mb"):
                hw["ram"] = f"{teg_stats['ram_total_mb'] / 1024:.1f}GB"
            hw.update(teg_stats)
            containers = []
            for entry in ctrs_raw.split(";;"):
                entry = entry.strip()
                if entry:
                    parts = entry.split(":::")
                    if len(parts) == 3:
                        containers.append({"name": parts[0], "image": parts[1], "status": parts[2]})
            hw["containers"] = containers
            return hw
        except Exception:
            return {}

    def _ssh_amd(self, host_alias: str) -> Dict[str, Any]:
        cmd = (
            "cpu=$(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | xargs); "
            "cores=$(nproc); "
            "ram=$(free -m | awk 'NR==2{printf \"%.1fGB\", $2/1024}'); "
            "disk=$(df -h / | awk 'NR==2{print $2}'); "
            "gpu_util=$(cat /sys/class/drm/card1/device/gpu_busy_percent 2>/dev/null || echo ''); "
            "gpu_vram_used=$(cat /sys/class/drm/card1/device/mem_info_vram_used 2>/dev/null || echo ''); "
            "gpu_vram_total=$(cat /sys/class/drm/card1/device/mem_info_vram_total 2>/dev/null || echo ''); "
            "ctrs=$(docker ps --format '{{.Names}}:::{{.Image}}:::{{.Status}}' 2>/dev/null | tr '\\n' ';;' || echo ''); "
            "echo \"$cpu|$cores|$ram|$disk|$gpu_util|$gpu_vram_used|$gpu_vram_total|$ctrs\""
        )
        try:
            out = subprocess.check_output(
                ["ssh", "-o", "ConnectTimeout=3", "-o", "BatchMode=yes", host_alias, cmd],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            cpu, cores, ram, disk, gpu_util, gpu_vram_used, gpu_vram_total, ctrs_raw = out.split("|", 7)
            hw: Dict[str, Any] = {"cpu": cpu, "cores": int(cores), "ram": ram, "disk": disk}
            if gpu_util:
                hw["gpu"] = "AMD GPU"
                hw["gpu_util_pct"] = int(gpu_util)
            if gpu_vram_used and gpu_vram_total:
                hw["gpu_vram_used_mb"] = int(gpu_vram_used) // 1024**2
                hw["gpu_vram_total_mb"] = int(gpu_vram_total) // 1024**2
            containers = []
            for entry in ctrs_raw.split(";;"):
                entry = entry.strip()
                if entry:
                    parts = entry.split(":::")
                    if len(parts) == 3:
                        containers.append({"name": parts[0], "image": parts[1], "status": parts[2]})
            hw["containers"] = containers
            return hw
        except Exception:
            return {}

    def _ping(self, ip: str) -> Optional[float]:
        try:
            out = subprocess.check_output(
                ["ping", "-c", "1", "-W", "1", ip],
                stderr=subprocess.DEVNULL, text=True
            )
            m = re.search(r"time=([\d.]+)", out)
            return round(float(m.group(1)), 1) if m else 0.0
        except subprocess.CalledProcessError:
            return None

    def get_nodes(self) -> List[Dict[str, Any]]:
        try:
            out = subprocess.check_output(["tailscale", "status", "--json"], text=True)
            data = json.loads(out)
        except Exception:
            return []

        raw = []
        self_node = data.get("Self", {})
        if self_node:
            raw.append({
                "name": self_node.get("HostName", ""),
                "ip": self_node.get("TailscaleIPs", [""])[0],
                "os": self_node.get("OS", ""),
                "self": True,
            })
        seen_names = set()
        for peer in data.get("Peer", {}).values():
            if peer.get("OS") == "iOS":
                continue
            if peer.get("HostName") in self.EXCLUDE_HOSTS:
                continue
            # De-duplicate by hostname: prefer linux over windows
            name = peer.get("HostName", "")
            os_ = peer.get("OS", "")
            if name in seen_names:
                continue
            if os_ == "windows" and any(
                p.get("HostName") == name and p.get("OS") == "linux"
                for p in data.get("Peer", {}).values()
            ):
                continue
            seen_names.add(name)
            raw.append({
                "name": peer.get("HostName", ""),
                "ip": peer.get("TailscaleIPs", [""])[0],
                "os": peer.get("OS", ""),
                "self": False,
            })

        from concurrent.futures import ThreadPoolExecutor
        def check(node):
            if node["self"]:
                node["latency_ms"] = 0.0
                node["reachable"] = True
                node["ssh_ok"] = True
                node["hardware"] = _local_hardware()
            else:
                node["latency_ms"] = self._ping(node["ip"])
                node["reachable"] = node["latency_ms"] is not None
                alias = self.SSH_HOSTS.get(node["ip"])
                if alias:
                    hw = self._ssh_hardware(alias, node["ip"])
                    node["hardware"] = hw
                    node["ssh_ok"] = bool(hw)  # True only if SSH returned data
                else:
                    node["hardware"] = {}
                    node["ssh_ok"] = None  # no SSH configured for this node
            return node

        with ThreadPoolExecutor(max_workers=12) as ex:
            nodes = list(ex.map(check, raw))

        nodes.sort(key=lambda n: (not n["reachable"], n.get("latency_ms") or 9999))
        return nodes


class HardwareService:
    def get_gpu_utilization(self) -> Dict[str, Any]:
        # AMD via sysfs
        busy = Path("/sys/class/drm/card1/device/gpu_busy_percent")
        vram_used_p = Path("/sys/class/drm/card1/device/mem_info_vram_used")
        vram_total_p = Path("/sys/class/drm/card1/device/mem_info_vram_total")
        if busy.exists():
            try:
                return {
                    "gpu_model": "AMD Radeon 780M",
                    "gpu_utilization_percent": int(busy.read_text().strip()),
                    "memory_used_mb": int(vram_used_p.read_text().strip()) // 1024**2,
                    "memory_total_mb": int(vram_total_p.read_text().strip()) // 1024**2,
                }
            except Exception:
                pass
        return {"error": "GPU unavailable"}


app = FastAPI(title="Krewe Dashboard API", version="1.0.0")

docker_svc = DockerService()
network_svc = NetworkService()
hardware_svc = HardwareService()
hive_svc = HiveService()


@app.get("/")
async def root():
    return FileResponse(
        DASHBOARD_DIR / "index.html",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/system/docker/containers")
async def get_docker_context():
    return {"containers": docker_svc.get_running_containers()}


@app.get("/system/network")
async def get_network_context():
    return {"interfaces": network_svc.get_all_interfaces()}


@app.get("/system/hardware/gpu")
async def get_gpu_context():
    return {"metrics": hardware_svc.get_gpu_utilization()}


@app.get("/hive/nodes")
async def get_hive_nodes():
    return {"nodes": hive_svc.get_nodes()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
